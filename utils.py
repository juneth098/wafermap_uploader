# utils.py
import os
import hashlib
import sys

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from configs import DB_URI

# -------------------------
# Filesystem helpers
# -------------------------
def mkdir(path):
    os.makedirs(path, exist_ok=True)

def progress(total, current):
    if total:
        pct = round(current / total * 100, 2)
        bar = "#" * int(pct)
        sys.stdout.write(f"\r[{bar:<100}] {pct}%")
        sys.stdout.flush()

def format_zip_timestamp(ts: str) -> str:
    """
    Convert 'YYYY-MM-DD HH:MM:SS' -> 'YYYY/MM/DD HH:MM:SS'
    """
    if not ts:
        return ""
    from datetime import datetime
    dt = datetime.strptime(ts.strip(), "%Y-%m-%d %H:%M:%S")
    return dt.strftime("%Y/%m/%d %H:%M:%S")

def format_zip_timestamp_for_filename(ts: str) -> str:
    """
    Convert 'YYYY-MM-DD HH:MM:SS' -> 'YYYY/MM/DD HH:MM:SS'
    """
    if not ts:
        return ""
    from datetime import datetime
    dt = datetime.strptime(ts.strip(), "%Y-%m-%d %H:%M:%S")
    return dt.strftime("%Y%m%d%H%M%S")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.digest()