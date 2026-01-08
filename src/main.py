# main.py
import os
import shutil
import zipfile
import sys
from datetime import datetime
from sqlalchemy import select, and_

from configs import PRODUCT_TO_CHECK, NAS_MAP_DIR, TEMP_DL_DIR, ROOT_DIR, FTP_BASE_URL, FTP_USERPWD, FTP_HOST
from db import (
    get_factory_info,
    upsert_upload,
    create_upload_session,
    create_factory_session,
    upload_table
)
from scanner import scan_maps
from umc_writer import process_wafer
from ftp_client import FTPClient, MAX_FTP_RETRIES
from utils import html_diff
from mailer import send_completion_mail, to_list

# Create single FTP connection
ftp = FTPClient(FTP_BASE_URL)

# ============================================================
# Step 0: Clean working directories
# ============================================================
for dir_to_clean in [TEMP_DL_DIR, ROOT_DIR]:
    if os.path.exists(dir_to_clean):
        print(f"[CLEANUP] Removing old files in {dir_to_clean}")
        shutil.rmtree(dir_to_clean)
    os.makedirs(dir_to_clean, exist_ok=True)

# ============================================================
# Step 1: DB Session (ONE session for whole run)
# ============================================================
db_session = create_upload_session()
fr_session = create_factory_session()

# Ensure TEMP_DL_DIR exists
os.makedirs(TEMP_DL_DIR, exist_ok=True)

# ============================================================
# Step 2: Scan NAS ZIPs
# ============================================================
print("Scanning NAS directory:", NAS_MAP_DIR)

not_uploaded_wafermaps = []
lots = []
first_scan_line = []

wafermap_to_upload = 0
total_wafer = 0
uploaded_count = 0
not_uploaded_count = 0
uploaded_wafers = 0
db_update_count = 0
item_count = 0
error_count = 0

for zip_file in os.listdir(NAS_MAP_DIR):
    if not zip_file.lower().endswith(".zip"):
        continue

    try:
        for zip_path_inner, txt_file, lot, wafer, stage, product in scan_maps(NAS_MAP_DIR):
            if os.path.basename(zip_path_inner) != zip_file:
                continue
            if product != PRODUCT_TO_CHECK:
                continue

            total_wafer += 1
            lot_prefix = lot.split(".")[0]

            record = db_session.execute(
                select(upload_table.c.id).where(
                    and_(
                        upload_table.c.Lot_Number.like(f"{lot_prefix}%"),
                        upload_table.c.Wafer_Id == int(wafer),
                        upload_table.c.stage == stage
                    )
                )
            ).first()

            if record:
                uploaded_count += 1
                status = "UPLOADED"
            else:
                not_uploaded_count += 1
                status = "NOT_UPLOADED"
                not_uploaded_wafermaps.append({
                    "zip_file": zip_file,
                    "txt_file": txt_file,
                    "lot": lot_prefix,
                    "wafer": wafer,
                    "stage": stage,
                    "product": product,
                })
            wafer_results_tbl = f"{PRODUCT_TO_CHECK} | Lot={lot} | W{wafer} | {stage} | {status}"
            print(wafer_results_tbl)
            first_scan_line.append(wafer_results_tbl)

    except zipfile.BadZipFile:
        error_count += 1
        print("Bad ZIP file, skipping:", zip_file)
        sys.exit(1)  # stop script immediately

# ============================================================
# Summary
# ============================================================
wafer_summary = f"""
Upload status summary for, {PRODUCT_TO_CHECK}
Total wafers scanned: {total_wafer}
Uploaded: {uploaded_count}
Not uploaded: {not_uploaded_count}
"""
# Append each line separately
for line in wafer_summary.strip().split("\n"):
    first_scan_line.append(line)
# ============================================================
# Step 4: Copy ZIPs that contain NOT_UPLOADED wafermaps
# ============================================================
if not not_uploaded_wafermaps:
    print("\nAll wafermaps are already UPLOADED.")
else:
    zip_to_process = {w["zip_file"] for w in not_uploaded_wafermaps}

    for zip_file in zip_to_process:
        shutil.copy2(
            os.path.join(NAS_MAP_DIR, zip_file),
            os.path.join(TEMP_DL_DIR, zip_file),
        )

    print(f"\nProcessing {len(zip_to_process)} ZIPs containing {len(not_uploaded_wafermaps)} NOT_UPLOADED wafermaps...")

    # ========================================================
    # Step 5: Process only NOT_UPLOADED wafermaps
    # ========================================================
    for item in not_uploaded_wafermaps:
        item_count += 1
        zip_file = item["zip_file"]
        txt_name = os.path.basename(item["txt_file"])
        lot = item["lot"]
        wafer = item["wafer"]
        stage = item["stage"]

        print(f"\n----- {item_count}/{len(not_uploaded_wafermaps)} -----")

        zip_path = os.path.join(TEMP_DL_DIR, zip_file)
        parts = zip_file.replace(".map.zip", "").split("_")
        zip_timestamp = (
            datetime.strptime("_".join(parts[2:8]), "%Y_%m_%d_%H_%M_%S")
            .strftime("%Y-%m-%d %H:%M:%S")
            if len(parts) >= 8
            else ""
        )

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                extract_dir = os.path.join(TEMP_DL_DIR, "extracted", lot, stage)
                os.makedirs(extract_dir, exist_ok=True)
                zf.extractall(extract_dir)

                for root, _, files in os.walk(extract_dir):
                    if txt_name not in files:
                        continue

                    txt_path = os.path.join(root, txt_name)

                    factory_info = get_factory_info(fr_session, lot, wafer, PRODUCT_TO_CHECK)

                    umc_file = process_wafer(
                        lot=lot,
                        wafer=wafer,
                        filename=txt_path,
                        product=PRODUCT_TO_CHECK,
                        stage=stage,
                        zip_timestamp=zip_timestamp,
                        factory_info=factory_info,
                    )

                    lots.append(lot)

                    # ============================
                    # FTP Upload using single connection
                    # ============================
                    if ftp.upload_and_verify(umc_file, max_retries=MAX_FTP_RETRIES):
                        uploaded_wafers += 1
                        # -------------------------
                        # Update DB only if FTP succeeded
                        # -------------------------
                        success = upsert_upload(db_session, upload_table, PRODUCT_TO_CHECK, lot, wafer, stage)
                        if success:
                            db_update_count += 1
                        else:
                            print(f"[WARN] Failed to insert/update DB for {lot} W{wafer} {stage}")
                            error_count += 1
                            sys.exit(1)  # stop script immediately
                    else:
                        print(f"[WARN] FTP upload failed for wafer {wafer}, DB not updated")
                        error_count += 1
                        sys.exit(1)  # stop script immediately


        except zipfile.BadZipFile:
            error_count += 1
            print("Bad ZIP file, skipping:", zip_file)
            sys.exit(1)  # stop script immediately

if not_uploaded_count != 0:

    wafermap_to_upload = not_uploaded_count
    total_wafer = 0
    uploaded_count = 0
    not_uploaded_count = 0

    second_scan_line=[]

    for zip_file in os.listdir(NAS_MAP_DIR):
        if not zip_file.lower().endswith(".zip"):
            continue

        try:
            for zip_path_inner, txt_file, lot, wafer, stage, product in scan_maps(NAS_MAP_DIR):
                if os.path.basename(zip_path_inner) != zip_file:
                    continue
                if product != PRODUCT_TO_CHECK:
                    continue

                total_wafer += 1
                lot_prefix = lot.split(".")[0]

                record = db_session.execute(
                    select(upload_table.c.id).where(
                        and_(
                            upload_table.c.Lot_Number.like(f"{lot_prefix}%"),
                            upload_table.c.Wafer_Id == int(wafer),
                            upload_table.c.stage == stage
                        )
                    )
                ).first()

                if record:
                    uploaded_count += 1
                    status = "UPLOADED"
                else:
                    not_uploaded_count += 1
                    status = "NOT_UPLOADED"
                    not_uploaded_wafermaps.append({
                        "zip_file": zip_file,
                        "txt_file": txt_file,
                        "lot": lot_prefix,
                        "wafer": wafer,
                        "stage": stage,
                        "product": product,
                    })
                wafer_results_tbl = f"{PRODUCT_TO_CHECK} | Lot={lot} | W{wafer} | {stage} | {status}"
                print(wafer_results_tbl)
                second_scan_line.append(wafer_results_tbl)

        except zipfile.BadZipFile:
            error_count += 1
            print("Bad ZIP file, skipping:", zip_file)
            sys.exit(1)  # stop script immediately

    # ============================================================
    # Summary
    # ============================================================
    wafer_summary = f"""
    Upload status summary for, {PRODUCT_TO_CHECK}
    Total wafers scanned: {total_wafer}
    Uploaded: {uploaded_count}
    Not uploaded: {not_uploaded_count}
    """

    # Append each line separately
    for line in wafer_summary.strip().split("\n"):
        second_scan_line.append(line)



    # ============================================================
    # Step 12: HTML Diff (Highlight newly uploaded wafers)
    # ============================================================
    html_diff(first_scan_line, second_scan_line)

# ============================================================
# Step 10: Email
# ============================================================
send_completion_mail(
    product=PRODUCT_TO_CHECK,
    lots=lots,
    total_wafers=wafermap_to_upload,
    uploaded_wafers=uploaded_wafers,
    db_update_count=db_update_count,
    ftp_dir=FTP_BASE_URL,
    to_list=to_list,
    error=error_count,
    has_attach = True if wafermap_to_upload != 0 else False
)

# ============================================================
# Step 11: Cleanup
# ============================================================
db_session.close()
fr_session.close()
ftp.close()
