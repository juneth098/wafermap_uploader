# utils.py
import hashlib
import os
import shutil
import sys
import difflib
from html import escape
import time

if getattr(sys, 'frozen', False):
    # Running from PyInstaller EXE
    BASE_DIR = sys._MEIPASS  # temp folder PyInstaller extracts to
    EXE_DIR = os.path.dirname(sys.executable)  # folder where EXE is located
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    EXE_DIR = BASE_DIR

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

# -------------------------
# SHA256 helper
# -------------------------
def sha256_file(file_path):
    """
    Calculate SHA256 hash of a file.
    """
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# -------------------------
# Side-by-side HTML diff
# -------------------------
diff_file = os.path.join(BASE_DIR, "wafer_upload_diff.html")



def html_diff(first_lines, second_lines):
    """
    Generate a side-by-side HTML diff highlighting differences.
    - Only changed characters in red
    - Added lines in green
    """
    html = []
    html.append("<html><head><style>")
    html.append("table {border-collapse: collapse; width: 100%;}")
    html.append("td {padding: 2px 4px; font-family: Consolas, monospace; vertical-align: top;}")
    html.append(".diff_add {background-color: #d0ffd0;}")   # green
    html.append(".diff_change {color: red;}")               # red font for changed characters
    html.append("</style></head><body><table border='1'>")

    # Pad both lists to same length
    max_len = max(len(first_lines), len(second_lines))
    first_lines += [""] * (max_len - len(first_lines))
    second_lines += [""] * (max_len - len(second_lines))

    for left, right in zip(first_lines, second_lines):
        if left == right:
            html.append(f"<tr><td>{escape(left)}</td><td>{escape(right)}</td></tr>")
        else:
            sm = difflib.SequenceMatcher(None, left, right)
            left_html = ""
            right_html = ""

            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                l_text = escape(left[i1:i2])
                r_text = escape(right[j1:j2])

                if tag == "equal":
                    left_html += l_text
                    right_html += r_text
                elif tag == "replace":
                    left_html += f"<span class='diff_change'>{l_text}</span>"
                    right_html += f"<span class='diff_change'>{r_text}</span>"
                elif tag == "delete":
                    left_html += f"<span class='diff_change'>{l_text}</span>"
                elif tag == "insert":
                    right_html += f"<span class='diff_change'>{r_text}</span>"

            html.append(f"<tr><td>{left_html}</td><td>{right_html}</td></tr>")

    html.append("</table></body></html>")

    output_file = diff_file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(html))

    print(f"[INFO] Side-by-side HTML diff saved to {output_file}")

    return output_file

# -------------------------
# Misc helpers
# -------------------------
def ensure_dir(path):
    """
    Ensure a directory exists.
    """
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def clean_dir(path):
    """
    Remove all files in a directory.
    """
    if os.path.exists(path):
        for root, dirs, files in os.walk(path):
            for f in files:
                os.remove(os.path.join(root, f))
            for d in dirs:
                shutil.rmtree(os.path.join(root, d))


def parse_soft_bins(soft_bin_str):
    """
    Convert CSV string to list of tuples [(0,"[]"), ...]
    """
    bins = []
    for line in soft_bin_str.strip().splitlines():
        if not line.strip():
            continue
        idx, desc = line.split(":", 1)
        bins.append((int(idx.strip()), desc.strip().strip('"')))
    return bins

##
def cleanup_duplicate(log_path):
#log_path = "unsupported_device.log"

    seen = set()
    unique_lines = []

    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line not in seen:
                seen.add(line)
                unique_lines.append(line)

    with open(log_path, "w", encoding="utf-8") as f:
        for line in unique_lines:
            f.write(line + "\n")

    print("[LOG] Duplicates removed")


# -----------------------------
# Safe copy function
# -----------------------------
def safe_copy(src, dst, retries=5):
    """Copy a file safely, creating destination folders if needed."""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    for attempt in range(1, retries + 1):
        try:
            shutil.copy2(src, dst)
            return True
        except (PermissionError, FileNotFoundError):
            if attempt == retries:
                raise
            time.sleep(attempt)  # simple backoff


# -----------------------------
# Your wait_until_stable function
# -----------------------------
def wait_until_stable(path, checks=3, delay=1):
    """
    Wait until file size stops changing.
    Returns True if file is stable, False otherwise.
    """
    last_size = -1
    for _ in range(checks):
        try:
            size = os.path.getsize(path)
        except FileNotFoundError:
            return False
        if size == last_size:
            return True
        last_size = size
        time.sleep(delay)
    return False