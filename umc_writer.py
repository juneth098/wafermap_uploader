# umc_writer.py
import os
import re
from string import Template
from configs import (
    ROOT_DIR, SUBCON_MAP,
    TESTER_DICT, TEST_PROGRAM_DICT,
    LOAD_BOARD_DICT, PROBE_CARD_DICT,
    DB_FACT_REPORT_TABLE, SOFT_BIN_DICT
)
from utils import (
    mkdir,
    format_zip_timestamp,
    format_zip_timestamp_for_filename
)

from db import create_session


# ------------------------
# UMC wafer header template
# ------------------------
umc_wafer_header_data = Template(
"[BOF]\n"
"    PRODUCT ID     : $product\n"
"    LOT ID         : $lot\n"
"    WAFER ID       : $wafer\n"
"    FLOW ID        : $flow\n"
"    START TIME     : $start_time\n"
"    STOP TIME      : $stop_time\n"
"    SUBCON         : $subcon\n"
"    TESTER NAME    : $tester_name\n"
"    TEST PROGRAM   : $test_program\n"
"    LOAD BOARD ID  : $load_board\n"
"    PROBE CARD ID  : $probe_card\n"
"    SITE NUM       : $site_num \n"
"    DUT ID         : $dut\n"
"    DUT DIFF NUM   : $dut_diff_num\n"
"    OPERATOR ID    : $operator\n"
"    TESTED DIE     : $gross_count\n"
"    PASS DIE       : $pass_count\n"
"    YIELD          : $yield_perc\n"
"    SOURCE NOTCH   : $probing_notch\n"
"    MAP ROW        : $map_row\n"
"    MAP COLUMN     : $map_col\n"
"    MAP BIN LENGTH : $map_bin_len\n"
"    SHIP           : $ship\n"
"     \n"
"    [SOFT BIN]\n"
"       BINNAME, DIENUM,  YIELD,MAPNAME,BINTYPE,DESCRIPTION\n"
)


def extract_notch(flat):
    """
    FLAT=180___(DOWN) -> DOWN
    """
    if not flat:
        return ""
    m = re.search(r"\((.*?)\)", flat)
    return m.group(1) if m else flat


def process_wafer(lot, wafer, filename, product, stage, zip_timestamp=None):
    """
    Convert wafer map TXT into UMC format.
    """
    print(f"[UMC WRITER] Processing file: {filename}")
    print(f"[UMC WRITER] Stage: {stage}")

    # ------------------------
    # Parse wafer TXT
    # ------------------------
    wafer_map_lines = []
    txt = {}
    with open(filename, "r", errors="ignore") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                txt[k.strip()] = v.strip()
            elif "." in line or "#" in line or "~" in line:
                wafer_map_lines.append(line)
    # Extract wafer ID
    wafer_txt = txt.get("WAFER_ID", "")
    wafer_part =wafer_txt.split("-")[0] if "-" in wafer_txt else wafer_txt
    wafer_id =wafer_part[-2:]

    # Extract YIELD from wafermap
    yield_perc = txt.get("TEST_YIELD", "0%").strip()
    if not yield_perc.endswith("%"):
        yield_perc += "%"


    total_test = int(txt.get("TOTAL_TEST", 0))
    total_pass = int(txt.get("TOTAL_PASS", 0))
    yield_pct = (total_pass * 100 / total_test) if total_test else 0
    probing_notch = extract_notch(txt.get("FLAT", ""))

    # ------------------------
    # Factory report lookup
    # ------------------------
    session = create_session()
    from sqlalchemy import Table, MetaData

    schema, table = DB_FACT_REPORT_TABLE.split(".")
    metadata = MetaData()
    factory = Table(
        table,
        metadata,
        schema=schema,
        autoload_with=session.bind
    )

    lot_prefix = lot.split(".")[0]


    product_wildcard = product.split("-")[0]
    row = session.query(factory).filter(
        factory.c.Lot_No.like(f"{lot_prefix}%.%"),
        factory.c.ID == wafer,
        factory.c.Product.like(f"{product_wildcard}%")
    ).one_or_none()

    if row:
        machine = getattr(row, "Machine", "")
        program = getattr(row, "Program", "")
        operator = getattr(row, "Operator", "")
        operator_class = getattr(row, "Class", "")
        operator_class = operator_class[:1] if machine else ""
        operator_id = f"{operator_class}-{operator}" if operator else ""
    else:
        machine = ""
        program = ""
        operator_id = ""

    # ------------------------
    # Header fields
    # ------------------------
    subcon = SUBCON_MAP.get(product, "GREATEK TAIWAN")
    tester_name = f"{TESTER_DICT.get(product, '')} {machine}".strip()
    test_program = program or TEST_PROGRAM_DICT.get(product, "")
    load_board = LOAD_BOARD_DICT.get(product, "")
    probe_card = PROBE_CARD_DICT.get(product, "RP923/1")
    start_time = format_zip_timestamp(zip_timestamp)
    # ------------------------
    # Output path
    # ------------------------
    out_dir = os.path.join(ROOT_DIR, lot_prefix, stage)

    mkdir(out_dir)
    timestamp_filename = format_zip_timestamp_for_filename(zip_timestamp)
    umc_name = f"{lot_prefix}{str(wafer).zfill(2)}_{timestamp_filename}.{stage}.umc"
    umc_path = os.path.join(out_dir, umc_name)
    print(umc_path)
    if os.path.exists(umc_path):
        os.remove(umc_path)

    # ------------------------
    # Generate soft-bin section
    # ------------------------
    soft_bins = SOFT_BIN_DICT.get(product, [])
    soft_bin_lines = []

    for b, desc in soft_bins:
        if b > 9:
            continue  # only convert bins 0-9

        # Try to get count from TXT (BIN01(1), BIN02(2), ...)
        txt_key = f"BIN{str(b).zfill(2)}({b if b <= 9 else chr(64 + b)})"
        dienum = int(txt.get(txt_key, 0))

        # Yield per bin = count / total_test
        bin_yield = (dienum / total_test * 100) if total_test else 0.0
        bin_yield_str = f"{bin_yield:.2f}%"

        # Format line
        line = f"    BIN,      {b}, {dienum:>6}, {bin_yield_str:>6}, {{{desc}}}"
        soft_bin_lines.append(line)


    # ------------------------
    # Convert wafer map to UMC soft bin map format
    # ------------------------

    map_lines = ["".join(c if c.isalnum() else " " for c in line) for line in wafer_map_lines]

    # ------------------------
    # Step 3: Trim empty rows (rows without alphanum)
    # ------------------------
    # Find first and last row with at least one alphanumeric character
    first_row = next(i for i, line in enumerate(map_lines) if any(c.isalnum() for c in line))
    last_row = len(map_lines) - 1 - next(
        i for i, line in enumerate(reversed(map_lines)) if any(c.isalnum() for c in line))
    map_lines = map_lines[first_row:last_row + 1]

    # ------------------------
    # Step 4: Trim empty columns (columns without alphanum)
    # ------------------------
    num_cols = max(len(line) for line in map_lines)
    first_col = next(i for i in range(num_cols) if any((i < len(line) and line[i].isalnum()) for line in map_lines))
    last_col = num_cols - 1 - next(i for i in range(num_cols) if
                                   any((num_cols - 1 - i < len(line) and line[-1 - i].isalnum()) for line in map_lines))
    map_lines = [line[first_col:last_col + 1] for line in map_lines]

    # ------------------------
    # Step 5: Generate column header for trimmed width
    # ------------------------
    trimmed_width = last_col - first_col + 1
    col_line0 = "    " + "0" * trimmed_width
    col_line1 = "    " + "".join(str(((i + 1) // 10) % 10) for i in range(trimmed_width))
    col_line2 = "    " + "".join(str((i+1) % 10) for i in range(trimmed_width))

    # ------------------------
    # Step 6: Add row numbers (001,002,...) and prepare final map
    # ------------------------

    soft_bin_map_lines = ["[SOFT BIN MAP]", col_line0, col_line1, col_line2]
    soft_bin_map_lines.append(" ")
    for row_idx, line in enumerate(map_lines):
        row_number = f"{row_idx + 1:03}"
        soft_bin_map_lines.append(f"{row_number} {line}")

    soft_bin_map_lines.append(" ")
    soft_bin_map_lines.append("[EXTENSION]")
    soft_bin_map_lines.append(" ")
    soft_bin_map_lines.append("[EOF]")
    soft_bin_map_lines.append(" ")

    # ------------------------
    # Step 7: Save or print
    # ------------------------
    #umc_soft_bin_map = "\n".join(soft_bin_map_lines)
    #print(umc_soft_bin_map)

    # ------------------------
    # Write UMC
    # ------------------------
    with open(umc_path, "w") as f:
        f.write(
            umc_wafer_header_data.safe_substitute(
                product=product,
                lot=lot_prefix,
                wafer=wafer_id,
                flow=stage,
                start_time=start_time,
                stop_time="",
                subcon=subcon,
                tester_name=tester_name,
                test_program=test_program,
                load_board=load_board,
                probe_card=probe_card,
                operator=operator_id,
                gross_count=total_test,
                pass_count=total_pass,
                yield_perc=f"{yield_pct:.0f}%",
                probing_notch=probing_notch,
                site_num="",
                dut="",
                dut_diff_num="",
                #map_row=last_row,
                map_row=len(map_lines), #fixed for FT233H-B
                map_col=trimmed_width,
                map_bin_len="1",
                ship=""
            )
        )

        for l in soft_bin_lines:
            f.write(l + "\n")
        f.write(" \n")

        # ------------------------
        # Join lines into final string
        # ------------------------
        for l in soft_bin_map_lines:
            f.write(l + "\n")

    return umc_path
