# configs.py
import os
from dotenv import load_dotenv
import csv
import sys
from utils import parse_soft_bins

load_dotenv()



#script details
author = "Juneth Viktor Ellon Moreno"
script_ver = "1"

#Debug option
IS_TEST_DEBUG_MODE = True      #Enable only during Test
IS_PRODUCTION_MODE = False     #Enable only for Production Release (Will work only in actual Machine)

if IS_PRODUCTION_MODE == IS_TEST_DEBUG_MODE:
    print("Wrong Debug Mode")
    sys.exit(1)

# -------------------------
# Config
# -------------------------
PRODUCT_TO_CHECK = ""
if IS_TEST_DEBUG_MODE:
    PRODUCT_TO_CHECK = ""
    #PRODUCT_TO_CHECK = "FT4232H-C"  #Reference Product
    #PRODUCT_TO_CHECK = "FT233H-B"   #Target1
    #PRODUCT_TO_CHECK = "FT260-B"    #Target2


if getattr(sys, 'frozen', False):
    # Running from PyInstaller EXE
    BASE_DIR = sys._MEIPASS  # temp folder PyInstaller extracts to
    EXE_DIR = os.path.dirname(sys.executable)  # folder where EXE is located
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    EXE_DIR = BASE_DIR



# -------------------------
# PATHS
# -------------------------

#Path for the final wafermap output in UMC-format
if IS_PRODUCTION_MODE:
    ROOT_DIR = r"D:\UMC_log_Processing\files_for_FTP_processing\new_scheme_2018\FT232RV2"
if IS_TEST_DEBUG_MODE:
    ROOT_DIR = os.path.join(EXE_DIR, "converted_umc")
#Path for the raw wafer map to be converted
#NAS_MAP_DIR = r"M:\DOWNLOADED\CR_Micro\PROBE\MAP"      # REFERENCE contains wafermap from the OSAT
if IS_PRODUCTION_MODE:
    NAS_MAP_DIR = r"M:\DOWNLOADED\GREATEK\MAP"            # PRODUCTION
if IS_TEST_DEBUG_MODE:
    #NAS_MAP_DIR = os.path.join(BASE_DIR, "raw_wafer_map")# TEST Environment
    #NAS_MAP_DIR = r"./raw_wafer_map"  # TEST Environment
    NAS_MAP_DIR = os.path.join(EXE_DIR, "raw_wafer_map")


#Temporary path for processing the files
#TEMP_DL_DIR = r"D:\UMC_log_Processing\files_for_FTP_processing\new_scheme_2018\temp_dl_area"
TEMP_DL_DIR = os.path.join(EXE_DIR, "temp_dl")


# -------------------------
# DATABASE
# -------------------------
#DB Access
DB_URI = os.getenv("DB_URI")
if not DB_URI:
    raise RuntimeError("DB_URI not found in .env!")
#DB Status table
if IS_PRODUCTION_MODE:
    DB_UPLOAD_TABLE = "umc_uploaded_wafers.wafers_uploaded"                # PRODUCTION
if IS_TEST_DEBUG_MODE:
    DB_UPLOAD_TABLE = "umc_uploaded_wafers.wafers_uploaded_for_test_script" # TEST Environment
#DB Factory reports
DB_FACT_REPORT_TABLE = "factory_reports.gtk_cp_report_sg"               #


# -------------------------
# FTP
# -------------------------
#FTP Access
FTP_USERPWD = os.getenv("FTP_USERPWD")
if not FTP_USERPWD:
    raise RuntimeError("FTP_USERPWD not found in .env!")

FTP_HOST = "ftp1.umc.com"
#FTP destination path
if IS_PRODUCTION_MODE:
    FTP_BASE_URL = "ftp://tftdi@ftp1.umc.com/CP_S_UMC"               # PRODUCTION
if IS_TEST_DEBUG_MODE:
    FTP_BASE_URL = "ftp://tftdi@ftp1.umc.com/CP_S_UMC/test_dir_geoff" # TEST Environment


# -------------------------
# Load Product Configs from CSV
# -------------------------

PRODUCT_CSV = os.path.join(BASE_DIR, "product_config.csv")

if PRODUCT_TO_CHECK:
    # Normalize PRODUCT_TO_CHECK to a set
    if isinstance(PRODUCT_TO_CHECK, str):
        PRODUCTS_TO_LOAD = {PRODUCT_TO_CHECK}
    else:
        PRODUCTS_TO_LOAD = set(PRODUCT_TO_CHECK)

else:
    # PRODUCT_TO_CHECK not defined yet — first GUI run
    PRODUCTS_TO_LOAD = set()

PRODUCT_CONFIG = {"_device_to_product": {}}

# Load CSV only if PRODUCTS_TO_LOAD is not empty
if PRODUCTS_TO_LOAD:
    with open(PRODUCT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=",")

        for row in reader:
            product = row["PRODUCT"].strip()

            #  Skip products not requested
            if product not in PRODUCTS_TO_LOAD:
                continue

            device = row["DEVICE_NAME"].strip()

            PRODUCT_CONFIG["_device_to_product"][device] = product

            PRODUCT_CONFIG[product] = {
                "subcon": row["SUBCON"].strip(),
                "tester": row["TESTER"].strip(),
                "test_program": row["TEST_PROGRAM"].strip(),
                "load_board": row["LOAD_BOARD"].strip(),
                "probe_card": row["PROBE_CARD"].strip(),
                "soft_bins": parse_soft_bins(row["SOFT_BINS"]),
            }

    print(f"[CONFIG] Loaded products from CSV: {list(PRODUCTS_TO_LOAD)}")
