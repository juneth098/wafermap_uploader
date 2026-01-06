# scanner.py
import os
import zipfile
from configs import PRODUCT_CONFIG


DEVICE_TO_PRODUCT = PRODUCT_CONFIG["_device_to_product"]
# -------------------------
# Map wafer DEVICE_NAME to product
# -------------------------

def extract_wafer_from_filename(filename: str, lot_prefix: str):
    """
    filename: DKWJ301-A5.txt
    lot_prefix: DKWJ3

    returns:
      wafer_str -> '01'
      wafer_id  -> 1
    """
    name = os.path.splitext(filename)[0]   # DKWJ301-A5
    before_dash = name.split("-")[0]        # DKWJ301

    if not before_dash.startswith(lot_prefix):
        raise ValueError(f"[SCANNER] {filename} does not start with lot prefix {lot_prefix}")

    wafer_digits = before_dash[len(lot_prefix):]  # '01'
    wafer_id = int(wafer_digits)
    wafer_str = f"{wafer_id:02d}"

    return wafer_str, wafer_id


def extract_lot_from_zip(zip_name):
    """
    LOT rules:
    - Take substring before first '_'
    - If it contains '.', take substring before '.'
    """
    base = os.path.basename(zip_name)
    lot_part = base.split("_", 1)[0]
    lot = lot_part.split(".", 1)[0]
    return lot


def extract_stage_from_zip(zip_name):
    """
    Stage is CP1 or CP2 token in filename.
    """
    tokens = zip_name.upper().split("_")
    for t in tokens:
        if t in ("CP1", "CP2"):
            return t
    return "UNKNOWN"


def extract_wafer_from_txt(wafer_id):
    """
    Example:
        WAFER_ID=QT5KA03-1 → wafer = 3
    """
    if not wafer_id:
        return None

    wafer_part =wafer_id.split("-")[0] if "-" in wafer_id else wafer_id
    wafer_part =wafer_part[-2:]

    return wafer_part


def scan_maps(nas_dir):
    """
    Scan NAS directory for ZIP files.

    Yields:
        zip_path,
        txt_filename,
        lot,
        wafer,
        stage,
        product
    """
    for root, _, files in os.walk(nas_dir):
        for fname in files:
            if not fname.lower().endswith(".zip"):
                continue

            zip_path = os.path.join(root, fname)

            # -------------------------
            # LOT and STAGE from ZIP
            # -------------------------
            lot = extract_lot_from_zip(fname)
            stage = extract_stage_from_zip(fname)

            try:
                with zipfile.ZipFile(zip_path, "r") as zf:
                    for info in zf.infolist():
                        if not info.filename.lower().endswith(".txt"):
                            continue

                        with zf.open(info) as f:
                            lines = f.read().decode("utf-8", errors="ignore").splitlines()

                        txt = {}
                        for line in lines:
                            if "=" in line:
                                k, v = line.split("=", 1)
                                txt[k.strip()] = v.strip()

                        device_name = txt.get("DEVICE_NAME")
                        wafer_id = txt.get("WAFER_ID")

                        # -------------------------
                        # Map device to product
                        # -------------------------
                        product = DEVICE_TO_PRODUCT.get(device_name)
                        if not product:
                            continue

                        # -------------------------
                        # Wafer number
                        # -------------------------
                        wafer = extract_wafer_from_txt(wafer_id)
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
