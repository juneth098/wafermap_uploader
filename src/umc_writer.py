# umc_writer.py
import os
import re
from string import Template, digits
from configs import (
    ROOT_DIR, PRODUCT_CONFIG
)

from utils import (
    mkdir,
    format_zip_timestamp,
    format_zip_timestamp_for_filename
)


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
"           BIN NAME, DIENUM,  YIELD, DESCRIPTION\n"
)


def extract_notch(flat):
    """
    FLAT=180___(DOWN) -> DOWN
    """
    if not flat:
        return ""
    m = re.search(r"\((.*?)\)", flat)
    return m.group(1) if m else flat


def process_wafer_GTK(lot, wafer, filename, product, stage, zip_timestamp=None, factory_info=None):

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

    lot_prefix = lot.split(".")[0]

    product_wildcard = product.split("-")[0]
    factory_info = factory_info or {}
    machine = factory_info.get("machine", "")
    program = factory_info.get("program", "")
    operator = factory_info.get("operator", "")
    #operator_class = factory_info.get("Class", "")
    operator_id = factory_info.get("operator_id", "")

    cfg = PRODUCT_CONFIG.get(product)
    if not cfg:
        raise ValueError(f"Product {product} not found in PRODUCT_CONFIG")

    # ------------------------
    # Header fields
    # ------------------------
    subcon = cfg["subcon"]
    tester_name = f"{cfg["tester"]} {machine}"
    test_program = program or cfg["test_program"]
    load_board = cfg["load_board"]
    probe_card = cfg["probe_card"]
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
    soft_bins = cfg["soft_bins"]
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

def process_wafer_ASE(lot, wafer, filename, product, stage, zip_timestamp=None, factory_info=None):
    """
    Convert wafer map TXT into UMC format - supports old & new OSAT formats.
    """
    print(f"[UMC WRITER] Processing file: {filename}")
    print(f"[UMC WRITER] Stage: {stage}")

    # ── Read all lines once ─────────────────────────────────────────────────────
    all_lines = []
    with open(filename, "r", encoding="utf-8", errors="ignore") as f:
        all_lines = [line.rstrip('\n') for line in f]

    # ── Parse metadata, bin information, and map ────────────────────────────────
    metadata = {}
    wafer_map_raw = []
    bin_counts = {}
    bin_descriptions = {}
    in_map = False
    in_bin_count_table = False
    in_bin_desc_table = False
    bin_headers = []

    for line in all_lines:
        stripped = line.strip()

        if not stripped and not in_map:
            continue

        # Metadata
        if re.match(r'^[A-G]\.\s', line):
            _, rest = line.split('.', 1)
            if ':' in rest:
                k, v = rest.split(':', 1)
                metadata[k.strip()] = v.strip()
        elif re.match(r'^\d+\.\s', stripped) and ':' in stripped:
            _, rest = stripped.split('.', 1)
            if ':' in rest:
                k, v = rest.split(':', 1)
                metadata[k.strip()] = v.strip()
        elif '=' in line:
            k, v = line.split("=", 1)
            metadata[k.strip()] = v.strip()

        # Bin count table
        if "Bin Count & Yield" in stripped or "Lot Bin Count & Yield" in stripped:
            in_bin_count_table = True
            continue
        if in_bin_count_table:
            if stripped.startswith("BIN "):
                parts = re.split(r'\s+', stripped)
                bin_headers = [int(p) for p in parts[1:] if p.isdigit()]
                continue
            if stripped.startswith("COUNT "):
                parts = re.split(r'\s+', stripped)
                values = [int(x) for x in parts[1:] if x.isdigit()]
                if len(values) == len(bin_headers) + 1:
                    for b, cnt in zip(bin_headers, values[:-1]):
                        bin_counts[b] = cnt
                in_bin_count_table = False
                continue

        # Bin description table (we collect but don't use for description)
        if "Bin Description Yield" in stripped or stripped.startswith("NO. Bin"):
            in_bin_desc_table = True
            continue
        if in_bin_desc_table:
            if "===" in stripped:
                in_bin_desc_table = False
                continue
            m = re.match(r'^\s*(\d+)\s+(.+?)\s+([\d.]+%)$', stripped)
            if m:
                b = int(m.group(1))
                bin_descriptions[b] = m.group(2).strip()

        # Wafer map
        if "Wafer Map (In Hexadecimal Format)" in line:
            in_map = True
            continue

        if in_map:
            # skip only separator ruler lines
            if re.search(r'^\s*\+\|', line):
                continue

            # detect wafer row FIRST (do NOT skip before this)
            m = re.match(r'^\s*(\d+)\s*\|(.*)$', line)
            if m:
                content = m.group(2).rstrip()
                # preserve spacing → build fixed grid (ASE safe)
                cells = []
                i = 0
                while i < len(content):
                    chunk = content[i:i + 4]
                    hit = re.search(r'[0-9A-F]', chunk)
                    if hit:
                        cells.append(hit.group(0))
                    else:
                        cells.append(' ')
                    i += 4
                wafer_map_raw.append(''.join(cells))
                continue
            # stop map if extension starts
            if "[EXTENSION]" in line or "[EOF]" in line:
                in_map = False

    # ── Extract fields ──────────────────────────────────────────────────────────
    cfg = PRODUCT_CONFIG.get(product)
    if not cfg:
        raise ValueError(f"Product {product} not found in PRODUCT_CONFIG")

    dev_name = metadata.get("Device Name", product)
    product_id = dev_name.split(" ", 1)[0] if " " in dev_name else dev_name

    lot_raw = metadata.get("Lot No", lot)
    lot_prefix = lot_raw.split(".")[0]

    wafer_str = metadata.get("Wafer ID", str(wafer))
    wafer_id = wafer_str[-2:].zfill(2) if wafer_str.isdigit() else str(wafer).zfill(2)

    tester_no = metadata.get("Tester No", "")
    machine = factory_info.get("machine", "") if factory_info else ""
    tester_name = f"{cfg.get('tester', 'J750')} {tester_no or machine}".strip()

    operator_id = metadata.get("Operator Badge", factory_info.get("operator_id", ""))
    probe_card = metadata.get("Probe Card", cfg.get("probe_card", ""))
    test_program = metadata.get("Test Program", factory_info.get("program", cfg.get("test_program", "")))

    total_test = int(metadata.get("Die Per Wafer", metadata.get("TOTAL_TEST", "0")).split()[0] or "0")
    total_pass = int(metadata.get("Total Good Dices", metadata.get("TOTAL_PASS", "0")).split()[0] or "0")
    yield_pct = (total_pass * 100.0 / total_test) if total_test > 0 else 0.0
    yield_str = f"{int(round(yield_pct))}%"

    fn_loc = metadata.get("F/N Location", metadata.get("FLAT", ""))
    probing_notch = "DOWN" if "DOWN" in fn_loc.upper() else "UP"

    start_raw = metadata.get("Start Time", "")
    if start_raw and " " in start_raw:
        date_part, time_part = start_raw.split(" ", 1)
        date_part = date_part.replace("-", "/")
        start_time = f"{date_part} {time_part}"
    else:
        start_time = format_zip_timestamp(zip_timestamp) if zip_timestamp else ""

    # ── Soft bin section (using your config descriptions) ───────────────────────
    soft_bins = cfg["soft_bins"]

    soft_bin_lines = []
    for b, desc in soft_bins:
        if b > 9:
            continue
        count = bin_counts.get(b, 0)
        bin_yield = (count / total_test * 100.0) if total_test > 0 else 0.0
        line = f"    BIN, {b}, {count:>6}, {bin_yield:>6.2f}%, {{{desc}}}"
        soft_bin_lines.append(line)

    # ── Map processing ──────────────────────────────────────────────────────────
    if not wafer_map_raw:
        trimmed_map = []
        map_row_count = 0
        map_col_count = 0

    else:
        # ⭐ detect real die rows
        active_rows = [
            i for i, row in enumerate(wafer_map_raw)
            if any(c.isalnum() for c in row)
        ]

        if not active_rows:
            trimmed_map = []
            map_row_count = 0
            map_col_count = 0

        else:
            first_row = min(active_rows)
            last_row = max(active_rows)

            # ⭐ Y normalized slice
            map_lines = wafer_map_raw[first_row:last_row + 1]

            max_width = max(len(row) for row in map_lines)

            # ⭐ detect real die columns
            col_has_data = [False] * max_width
            for row in map_lines:
                for i, c in enumerate(row):
                    if c.isalnum():
                        col_has_data[i] = True

            first_col = next(i for i, v in enumerate(col_has_data) if v)
            last_col = max(i for i, v in enumerate(col_has_data) if v)

            # ⭐ X normalized slice
            trimmed_map = [
                row[first_col:last_col + 1].ljust(last_col - first_col + 1)
                for row in map_lines
            ]

            map_row_count = len(trimmed_map)
            map_col_count = last_col - first_col + 1
    # ── Ruler ───────────────────────────────────────────────────────────────────
    ruler1 = " " * 4 + "0" * map_col_count
    ruler2 = " " * 4 + "".join(str((i + 1) // 10) for i in range(map_col_count))
    ruler3 = " " * 4 + "".join(str((i + 1) % 10) for i in range(map_col_count))

    soft_bin_map_lines = ["[SOFT BIN MAP]"]

    if map_col_count > 0:
        soft_bin_map_lines.extend([ruler1, ruler2, ruler3])

    soft_bin_map_lines.append(" ")

    for idx, row in enumerate(trimmed_map, 1):
        soft_bin_map_lines.append(f"{idx:03} {row}")

    soft_bin_map_lines.extend([" ", "[EXTENSION]", " ", "[EOF]", " "])

    # ── Output ──────────────────────────────────────────────────────────────────
    out_dir = os.path.join(ROOT_DIR, lot_prefix, stage)
    mkdir(out_dir)
    timestamp_fn = format_zip_timestamp_for_filename(zip_timestamp)
    umc_name = f"{lot_prefix}{str(wafer).zfill(2)}_{timestamp_fn}.{stage}.umc"
    umc_path = os.path.join(out_dir, umc_name)
    print(umc_path)

    if os.path.exists(umc_path):
        os.remove(umc_path)

    with open(umc_path, "w", encoding="utf-8") as f:
        f.write(
            umc_wafer_header_data.safe_substitute(
                product=product_id,
                lot=lot_prefix,
                wafer=wafer_id,
                flow=stage,
                start_time=start_time,
                stop_time="",
                subcon=cfg["subcon"],
                tester_name=tester_name,
                test_program=test_program,
                load_board=cfg["load_board"],
                probe_card=probe_card,
                operator=operator_id,
                gross_count=total_test,
                pass_count=total_pass,
                yield_perc=yield_str,
                probing_notch=probing_notch,
                site_num="",
                dut="",
                dut_diff_num="",
                map_row=map_row_count,
                map_col=map_col_count,
                map_bin_len="1",
                ship=""
            )
        )

        for ln in soft_bin_lines:
            f.write(ln + "\n")
        f.write("\n")

        for ln in soft_bin_map_lines:
            f.write(ln + "\n")

    return umc_path