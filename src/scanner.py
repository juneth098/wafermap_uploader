# scanner.py
import os
import zipfile
from configs import PRODUCT_CONFIG
import sys

DEVICE_TO_PRODUCT = PRODUCT_CONFIG["_device_to_product"]
# -------------------------
# Map wafer DEVICE_NAME to product
# -------------------------

def extract_wafer_from_filename(filename: str, subcon):
    """
    filename: DKWJ301-A5.txt #GTK
    lot_prefix: DKWJ3

     filename: QTGAQ-CP1T0-CJ23016700-16.txt #ASE
    lot_prefix: QTGAQ

    returns:
      wafer_str -> '01'
      wafer_id  -> 1
    """
    name = os.path.splitext(filename)[0]   # DKWJ301-A5 or QTGAQ-CP1T0-CJ23016700-16
    if subcon == "GTK":
        lotid = name.split("-")[0]        # DKWJ301
        wafer_digits = lotid[:2]  # '01'

    else: #ASE
        wafer_digits = name.split("-")[-1]   #16

    wafer_id = int(wafer_digits)
    wafer_str = f"{wafer_id:02d}"

    return wafer_str, wafer_id


def extract_lot_from_zip(zip_name):
    """
    LOT rules:
    - Take substring before first '_'
    - If it contains '.', take substring before '.'
    zip filename = DKJR5.1_CP1_2021_08_23_08_34_47.map #GTK
                   QTGAQ_CP1_2025_7_9_10_10_00.map     #ASE
    """
    base = os.path.basename(zip_name)

    lot_part = base.split("_", 1)[0]  #DKJR5.1 or QTGAQ
    lot = lot_part.split(".", 1)[0]

    return lot


def extract_stage_from_zip(zip_name):
    """
    Stage is CP1 or CP2 token in filename.
    zip filename = DKJR5.1_CP1_2021_08_23_08_34_47.map #GTK
                   QTGAQ_CP1_2025_7_9_10_10_00.map     #ASE
    """

    tokens = zip_name.upper().split("_")

    for t in tokens:
        if t in ("CP1", "CP2"):
            return t
    return "UNKNOWN"


def extract_wafer_from_txt(wafer_id):
    """
    Example:
        WAFER_ID=QT5KA03-1 → wafer = 3 #GTK
        WAFER_ID=                      #ASE
    """
    if not wafer_id:
        return None

    wafer_part =wafer_id.split("-")[0] if "-" in wafer_id else wafer_id
    wafer_part =wafer_part[-2:]

    return wafer_part


def scan_maps(zip_path, unsupported_log = None, subcon ="GTK"):
    """
    Scan a single ZIP file.

    Yields:
        zip_path,
        txt_filename,
        lot,
        wafer,
        stage,
        product
    """

    fname = os.path.basename(zip_path)

    # -------------------------
    # LOT and STAGE from ZIP
    # -------------------------
    lot = extract_lot_from_zip(fname)
    stage = extract_stage_from_zip(fname)

    unsupported_devices = set()

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            for info in zf.infolist():
                if not info.filename.lower().endswith(".txt"):
                    continue
                with zf.open(info) as f:
                    lines = f.read().decode("utf-8", errors="ignore").splitlines()
                txt = {}
                if subcon == "GTK":
                    for line in lines:
                        if "=" in line:
                            k, v = line.split("=", 1)
                            txt[k.strip()] = v.strip()
                    device_name = txt.get("DEVICE_NAME")
                    wafer_id = txt.get("WAFER_ID")
                else: #ASE
                    for line in lines:
                        if "Device Name" in line:
                            device_name = line.split(":")[-1].strip(" ")
                # -------------------------
                # Map device to product
                # -------------------------
                product = DEVICE_TO_PRODUCT.get(device_name)
                if not product:
                    unsupported_devices.add(device_name)
                    #print(f"[SCAN] Product {device_name} not supported in product_config")
                    break
                # -------------------------
                # Wafer number
                # -------------------------
                if subcon == "GTK":
                    wafer = extract_wafer_from_txt(wafer_id)
                else: #ASE
                    wafer_str,wafer = extract_wafer_from_filename(info.filename,"ASE")
                if wafer is None:
                    continue
                yield (
                    zip_path,
                    info.filename,
                    lot,
                    wafer,
                    stage,
                    product,
                )
    except zipfile.BadZipFile:
        print(f"[SCANNER] Warning: Bad ZIP skipped: {zip_path}")
        sys.exit(1)  # stop script immediately

    # -------------------------
    # Write unsupported devices
    # -------------------------

    if unsupported_devices and unsupported_log:
        with open(unsupported_log, "a", encoding="utf-8") as f:
            for dev in sorted(unsupported_devices):
                #print("[SCANNER] Unsupported devices detected:", dev, unsupported_log)
                f.write(f"{dev}\n")