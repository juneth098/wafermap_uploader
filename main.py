# main.py
import os
import shutil
import zipfile
from datetime import datetime
from configs import PRODUCT_TO_CHECK, NAS_MAP_DIR, TEMP_DL_DIR, ROOT_DIR, FTP_BASE_URL
from db import open_upload_session, upsert_upload
from scanner import scan_maps
from umc_writer import process_wafer
from ftp_client import upload_and_verify, MAX_FTP_RETRIES, c, d
from mailer import send_completion_mail, to_list


# -------------------------
# Step 0: Clean TEMP_DL_DIR and ROOT_DIR before processing
# -------------------------
for dir_to_clean in [TEMP_DL_DIR, ROOT_DIR]:
    if os.path.exists(dir_to_clean):
        print(f"[CLEANUP] Removing old files in {dir_to_clean}")
        shutil.rmtree(dir_to_clean)
    os.makedirs(dir_to_clean, exist_ok=True)

# -------------------------
# DB Session
# -------------------------
session, upload_table = open_upload_session()

# Ensure TEMP_DL_DIR exists
os.makedirs(TEMP_DL_DIR, exist_ok=True)

# -------------------------
# Step 1: Scan NAS ZIPs and check upload status
# -------------------------
print("Scanning NAS directory:", NAS_MAP_DIR)

not_uploaded_zips = []
total_wafer = uploaded_count = not_uploaded_count = 0

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
        raise ValueError(f"{filename} does not start with lot prefix {lot_prefix}")

    wafer_digits = before_dash[len(lot_prefix):]  # '01'
    wafer_id = int(wafer_digits)
    wafer_str = f"{wafer_id:02d}"

    return wafer_str, wafer_id

for zip_file in os.listdir(NAS_MAP_DIR):
    if not zip_file.lower().endswith(".zip"):
        continue

    zip_path = os.path.join(NAS_MAP_DIR, zip_file)
    try:
        matched = False
        for zip_path_inner, txt_file, lot, wafer, stage, product in scan_maps(NAS_MAP_DIR):
            if os.path.basename(zip_path_inner) != zip_file:
                continue
            if product != PRODUCT_TO_CHECK:
                continue  # skip other products

            matched = True
            total_wafer += 1

            # Strip any ".00" suffix in lot for DB check
            lot_prefix = lot.split(".")[0]

            record = session.query(upload_table).filter(
                upload_table.c.Lot_Number.like(f"{lot_prefix}%"),
                upload_table.c.Wafer_Id == int(wafer),
                upload_table.c.stage == stage
            ).first()

            if record:
                uploaded_count += 1
                status = "UPLOADED"
            else:
                not_uploaded_count += 1
                status = "NOT_UPLOADED"
                if zip_file not in not_uploaded_zips:
                    not_uploaded_zips.append(zip_file)

            print(f"{PRODUCT_TO_CHECK} | Lot={lot} | W{wafer} | {stage} | {status}")

        if not matched:
            continue

    except zipfile.BadZipFile:
        print("Bad ZIP file, skipping:", zip_path)

# ------------------------
# Summary
# ------------------------
print("\nUpload status summary for", PRODUCT_TO_CHECK)
print(f"Total wafers scanned: {total_wafer}")
print(f"Uploaded: {uploaded_count}")
print(f"Not uploaded: {not_uploaded_count}")

# ------------------------
# Step 2: Copy NOT_UPLOADED ZIPs to TEMP_DL_DIR
# ------------------------
os.makedirs(TEMP_DL_DIR, exist_ok=True)

if not not_uploaded_zips:
    print("\nNo NOT_UPLOADED ZIPs found. Skipping copy and processing.")
else:
    for zip_file in not_uploaded_zips:
        src_zip = os.path.join(NAS_MAP_DIR, zip_file)
        dest_zip = os.path.join(TEMP_DL_DIR, zip_file)
        shutil.copy2(src_zip, dest_zip)

    # ------------------------
    # Step 3: Process all ZIPs in TEMP_DL_DIR
    # ------------------------
    print(f"\nProcessing {len(not_uploaded_zips)} NOT_UPLOADED ZIPs in TEMP_DL_DIR...")
    uploaded_wafers = 0
    for zip_file in os.listdir(TEMP_DL_DIR):
        if not zip_file.lower().endswith(".zip"):
            continue

        zip_path = os.path.join(TEMP_DL_DIR, zip_file)

        # Extract lot, stage, timestamp from ZIP filename
        parts = zip_file.replace(".map.zip", "").split("_")
        lot = parts[0].split(".")[0]  # remove any .00
        stage = parts[1].upper() if len(parts) > 1 else "UNKNOWN"
        zip_timestamp = "_".join(parts[2:8]) if len(parts) >= 8 else None
        zip_timestamp = datetime.strptime(zip_timestamp, "%Y_%m_%d_%H_%M_%S").strftime("%Y-%m-%d %H:%M:%S") if zip_timestamp else ""

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                extract_dir = os.path.join(TEMP_DL_DIR, "extracted", lot, stage)
                os.makedirs(extract_dir, exist_ok=True)
                zf.extractall(extract_dir)

                for root, _, files in os.walk(extract_dir):
                    for f in files:
                        if not f.lower().endswith(".txt"):
                            continue
                        wafer_str, wafer = extract_wafer_from_filename(f, lot_prefix=lot)

                        # ------------------------
                        # Process wafer (generate UMC)
                        # ------------------------

                        umc_file = process_wafer(
                            lot=lot,
                            wafer=wafer,
                            filename=os.path.join(root, f),
                            product=PRODUCT_TO_CHECK,
                            stage=stage,
                            zip_timestamp=zip_timestamp
                        )

                        # ------------------------
                        # Upload immediately to FTP
                        # ------------------------
                        umc_basename = os.path.basename(umc_file)
                        remote_url = f"{FTP_BASE_URL}/{umc_basename}"
                        local_dl_verify = os.path.join(TEMP_DL_DIR, f"verify_{umc_basename}")

                        if not upload_and_verify(c, d, umc_file, FTP_BASE_URL, TEMP_DL_DIR, MAX_FTP_RETRIES):
                            continue

                        # ------------------------
                        # Update DB immediately
                        # ------------------------

                        success = upsert_upload(
                            session=session,
                            upload_table=upload_table,
                            product=PRODUCT_TO_CHECK,
                            lot=lot,
                            wafer=wafer,
                            stage=stage
                        )
                        if success:
                            uploaded_wafers += 1
                        else:
                            print(f"[WARN] Failed to insert/update DB for {lot} W{wafer} {stage}")

        except zipfile.BadZipFile:
            print("Bad ZIP file, skipping:", zip_path)

# Send notification
send_completion_mail(
    product=PRODUCT_TO_CHECK,
    total_wafers=not_uploaded_count,
    uploaded_wafers=uploaded_wafers,
    ftp_dir=FTP_BASE_URL,
    to_list=to_list,
    #cc_list=cc_list,
    #attachments=attachments
)