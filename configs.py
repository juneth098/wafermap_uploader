# configs.py
import os
from dotenv import load_dotenv

load_dotenv()

# -------------------------
# CONFIG
# -------------------------
#PRODUCT_TO_CHECK = "FT4232H-C"  #Reference Product
#PRODUCT_TO_CHECK = "FT233H-B"   #Target1
PRODUCT_TO_CHECK = "FT260-B"    #Target2

# -------------------------
# PATHS
# -------------------------

#Path for the final wafermap output in UMC-format
#ROOT_DIR = r"D:\UMC_log_Processing\files_for_FTP_processing\new_scheme_2018\FT232RV2"
ROOT_DIR = r".\converted_umc" #test environment

#Path for the raw wafer map to be converted
#NAS_MAP_DIR = r"M:\DOWNLOADED\CR_Micro\PROBE\MAP"      # REFERENCE contains wafermap from the OSAT
#NAS_MAP_DIR = r"M:\DOWNLOADED\GREATEK\MAP"            # PRODUCTION
NAS_MAP_DIR = r".\raw_wafer_map"                       # TEST Environment

#Temporary path for processing the files
#TEMP_DL_DIR = r"D:\UMC_log_Processing\files_for_FTP_processing\new_scheme_2018\temp_dl_area"
TEMP_DL_DIR = r".\temp_dl"

# -------------------------
# DATABASE
# -------------------------
#DB Access
DB_URI = os.getenv("DB_URI")
if not DB_URI:
    raise RuntimeError("DB_URI not found in .env!")
#DB Status table
#DB_UPLOAD_TABLE = "umc_uploaded_wafers.wafers_uploaded"                # PRODUCTION
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
#FTP_BASE_URL = "ftp://tftdi@ftp1.umc.com/CP_S_UMC"               # PRODUCTION
FTP_BASE_URL = "ftp://tftdi@ftp1.umc.com/CP_S_UMC/test_dir_geoff" # TEST Environment


# -------------------------
# HARD-CODED Configs
# -------------------------
PRODUCT_CONFIG = {
    # -----------------------
    # Raw wafer → product map
    # -----------------------
    "_device_to_product": {
        "FT232H_REVC DIE-AP": "FT232H-C",
        "FT233H REVB DIE-AP": "FT233H-B",
        "FT4232H REVC DIE-AP": "FT4232H-C",
        "FT260_REVB DIE-AP": "FT260-B",
    },

    # -----------------------
    # Product configurations
    # -----------------------
    "FT232H-C": {
        "subcon": "GREATEK TAIWAN",
        "tester": "CT_2009",
        "test_program": "ct2008prb_7.46",
        "load_board": "",
        "probe_card": "",
        "soft_bins": [
            (0, "[]"),
            (1, "[GOOD]"),
            (2, "[FAIL EFUSE]"),
            (3, "[FAIL CC]"),
            (4, "[FAIL DIGITAL]"),
            (5, "[FAIL OPEN SHORT]"),
            (6, "[]"),
            (7, "[]"),
            (8, "[]"),
            (9, "[]"),
        ],
    },

    "FT233H-B": {
        "subcon": "GREATEK TAIWAN",
        "tester": "J750",
        "test_program": "FT233H_X4SITES_CP_REV1P8_20220613",
        "load_board": "",
        "probe_card": "",
        "soft_bins": [
            (0, "[]"),
            (1, "[GOOD]"),
            (2, "[FAIL EFUSE]"),
            (3, "[FAIL CC]"),
            (4, "[FAIL DIGITAL]"),
            (5, "[FAIL OPEN SHORT]"),
            (6, "[]"),
            (7, "[]"),
            (8, "[]"),
            (9, "[]"),
        ],
    },

    "FT4232H-C": {
        "subcon": "GREATEK TAIWAN",
        "tester": "CT_2009",
        "test_program": "ct2008prb_7.46",
        "load_board": "",
        "probe_card": "RP923/1",
        "soft_bins": [
            (0, "[]"),
            (1, "[GOOD]"),
            (2, "[FAIL POWER]"),
            (3, "[FAIL DIGITAL]"),
            (4, "[OTHERS]"),
            (5, "[REGULATOR FAIL]"),
            (6, "[]"),
            (7, "[]"),
            (8, "[]"),
            (9, "[]"),
        ],
    },

    "FT260-B": {
        "subcon": "GREATEK TAIWAN",
        "tester": "J750",
        "test_program": "FT260_CP_01_20160105",
        "load_board": "",
        "probe_card": "",
        "soft_bins": [
            (0, "[]"),
            (1, "[GOOD]"),
            (2, "[]"),
            (3, "[]"),
            (4, "[FAIL POWER SHORTS]"),
            (5, "[FAIL OPEN SHORT]"),
            (6, "[FAIL LEAKAGE]"),
            (7, "[FAIL DIGITAL]"),
            (8, "[FAIL PU PD]"),
            (9, "[]"),
        ],
    },
}
