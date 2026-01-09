# main.py
import os
import shutil
import zipfile
import sys
from datetime import datetime
from sqlalchemy import select, and_

from configs import (
    NAS_MAP_DIR, 
    TEMP_DL_DIR, 
    ROOT_DIR, 
    FTP_BASE_URL
)
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


def run_main(product_to_check = None):
    """Run wafermap upload process for a given product."""
    if not product_to_check:
        print("[ERROR] No product specified")
        return

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
    # Step 1: DB Session
    # ============================================================
    db_session = create_upload_session()
    fr_session = create_factory_session()
    os.makedirs(TEMP_DL_DIR, exist_ok=True)

    try:
        # ============================================================
        # Step 2: Scan NAS ZIPs
        # ============================================================
        print("Scanning NAS directory:", NAS_MAP_DIR)

        not_uploaded_wafermap = []
        lots = []
        first_scan_line = []

        total_wafer = 0
        uploaded_count = 0
        not_uploaded_count = 0
        uploaded_wafers = 0
        db_update_count = 0
        error_count = 0

        diff_file_path = None
        attach_bool = False

        for zip_file in os.listdir(NAS_MAP_DIR):
            if not zip_file.lower().endswith(".zip"):
                continue

            try:
                for zip_path_inner, txt_file, lot, wafer, stage, product in scan_maps(NAS_MAP_DIR):
                    if os.path.basename(zip_path_inner) != zip_file:
                        continue
                    if product != product_to_check:
                        continue

                    total_wafer += 1 #Counts number of wafer_results_tbl
                    lot_prefix = lot.split(".")[0] #ex. DNY1F.00 -> DNY1F

                    #Check database if the combination of LOT,Wafer,CP is already uploaded
                    record = db_session.execute(
                        select(upload_table.c.id).where(
                            and_(
                                upload_table.c.Lot_Number.like(f"{lot_prefix}%"),
                                upload_table.c.Wafer_Id == int(wafer),
                                upload_table.c.stage == stage
                            )
                        )
                    ).first()

                    if record: #Already in the database
                        uploaded_count += 1 #count the uploaded wafermap with the same lot
                        status = "UPLOADED"
                    else:
                        not_uploaded_count += 1  #count the 'to upload' wafermap with the same lot
                        status = "NOT_UPLOADED"
                        not_uploaded_wafermap.append({
                            "zip_file": zip_file,
                            "txt_file": txt_file,
                            "lot": lot_prefix,
                            "wafer": wafer,
                            "stage": stage,
                            "product": product,
                        })
                    wafer_results_tbl = f"{product_to_check} | Lot={lot} | W{wafer} | {stage} | {status}"
                    print(wafer_results_tbl)
                    first_scan_line.append(wafer_results_tbl)

            except zipfile.BadZipFile:
                error_count += 1
                print("Bad ZIP file, skipping:", zip_file)
                sys.exit(1)

        # ============================================================
        # Summary
        # ============================================================
        wafer_summary = f"""
        Upload status summary for {product_to_check}
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
        if not not_uploaded_wafermap: #Skip FTP upload and DB update Process
            print("\nAll wafermaps are already UPLOADED.")
        else:
            zip_to_process = {w["zip_file"] for w in not_uploaded_wafermap} #Gets the Zip file name for all target wafermap

            for zip_file in zip_to_process: #Copy all target zip into a temporary directory : ./temp_dl
                shutil.copy2(
                    os.path.join(NAS_MAP_DIR, zip_file),       #source
                    os.path.join(TEMP_DL_DIR, zip_file),       #destination
                )

            print(f"\nProcessing {len(zip_to_process)} ZIPs containing {len(not_uploaded_wafermap)} NOT_UPLOADED wafermaps...")

           # ========================================================
           # Step 5: Process only NOT_UPLOADED wafermaps
           # ========================================================
            for item_count, item in enumerate(not_uploaded_wafermap, start=1):
                zip_file = item["zip_file"]
                txt_name = os.path.basename(item["txt_file"])
                lot = item["lot"]
                wafer = item["wafer"]
                stage = item["stage"]

                print(f"\n----- {item_count}/{len(not_uploaded_wafermap)} -----")

                zip_path = os.path.join(TEMP_DL_DIR, zip_file)
                parts = zip_file.replace(".map.zip", "").split("_") #Ex: DKWJ3.1_CP1_2025_11_09_17_41_12.map.zip
                zip_timestamp = ( #Extract the timestamp from the zip filename
                    datetime.strptime("_".join(parts[2:8]), "%Y_%m_%d_%H_%M_%S")
                    .strftime("%Y-%m-%d %H:%M:%S")
                    if len(parts) >= 8
                    else ""
                )

                try:
                    with zipfile.ZipFile(zip_path, "r") as zf: #opens the zip
                        extract_dir = os.path.join(TEMP_DL_DIR, "extracted", lot, stage)
                        os.makedirs(extract_dir, exist_ok=True)
                        zf.extractall(extract_dir) #extract the zip file with different folder according to lot and stage ex. \temp_dl\extracted\DNCYK\CP2

                        for root_dir, _, files in os.walk(extract_dir):
                            if txt_name not in files:
                                continue

                            txt_path = os.path.join(root_dir, txt_name)
                            #reads the factory reports DB to get the default values
                            factory_info = get_factory_info(fr_session, lot, wafer, product_to_check)
                            #converts raw wafermap into UMC Format
                            umc_file = process_wafer(
                                lot=lot,
                                wafer=wafer,
                                filename=txt_path,
                                product=product_to_check,
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
                                success = upsert_upload(db_session, upload_table, product_to_check, lot, wafer, stage)
                                if success:
                                    db_update_count += 1
                                else:
                                    print(f"[WARN] Failed DB update for {lot} W{wafer} {stage}")
                                    error_count += 1
                                    sys.exit(1)
                            else:
                                print(f"[WARN] FTP upload failed for wafer {wafer}")
                                error_count += 1
                                sys.exit(1)

                except zipfile.BadZipFile:
                    error_count += 1
                    print("Bad ZIP file, skipping:", zip_file)
                    sys.exit(1)

        #Second scan to check for the DIFF - reads the DB and print summary. lastly, create diff file
        if not_uploaded_count != 0: #if there are wafermaps need to be uploaded

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
                        if product != product_to_check:
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
                            not_uploaded_wafermap.append({
                                "zip_file": zip_file,
                                "txt_file": txt_file,
                                "lot": lot_prefix,
                                "wafer": wafer,
                                "stage": stage,
                                "product": product,
                            })
                        wafer_results_tbl = f"{product_to_check} | Lot={lot} | W{wafer} | {stage} | {status}"
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
            Upload status summary for {product_to_check}
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

            if len(not_uploaded_wafermap) != 0:
                diff_file_path = html_diff(first_scan_line, second_scan_line)
                attach_bool = True

        # ============================================================
        # Step 4: Send email
        # ============================================================
        send_completion_mail(
            product=product_to_check,
            lots=lots,
            total_wafers=len(not_uploaded_wafermap),
            uploaded_wafers=uploaded_wafers,
            db_update_count=db_update_count,
            ftp_dir=FTP_BASE_URL,
            reciepient_list=to_list,
            error=error_count,
            has_attach=attach_bool,
            attachments = diff_file_path
        )
    finally:
        # ============================================================
        # Step 5: Cleanup
        # ============================================================
        db_session.close()
        fr_session.close()
        ftp.close()
        print(f"[DONE] Process completed for {product_to_check}")


# ============================================================
# CLI entry
# ============================================================
if __name__ == "__main__":
    product_arg = sys.argv[1] if len(sys.argv) > 1 else ""
    run_main(product_arg)
