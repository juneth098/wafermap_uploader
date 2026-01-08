# ftp_client.py
import os
import time
import pycurl
from utils import sha256_file
from configs import FTP_USERPWD
import sys

MAX_FTP_RETRIES = 3

# -------------------------
# Create reusable curl objects for upload/download
# -------------------------
curl_upload = pycurl.Curl()
curl_upload.setopt(pycurl.USERPWD, FTP_USERPWD)
curl_upload.setopt(pycurl.VERBOSE, 0)

curl_download = pycurl.Curl()
curl_download.setopt(pycurl.USERPWD, FTP_USERPWD)
curl_download.setopt(pycurl.VERBOSE, 0)


class FTPClient:
    """
    FTP client using pycurl for upload + verification
    """

    def __init__(self, ftp_base_url, remote_dir="/"):
        self.ftp_base_url = ftp_base_url.rstrip("/")
        self.remote_dir = remote_dir

    def upload_and_verify(self, local_file, max_retries=MAX_FTP_RETRIES):
        """
        Uploads a file, downloads it back, and verifies SHA256.
        Returns True if successful.
        """
        basename = os.path.basename(local_file)
        remote_url = f"{self.ftp_base_url}/{basename}"
        temp_dir = os.path.dirname(local_file) or "."
        local_verify = os.path.join(temp_dir, f"verify_{basename}")

        # Upload
        if not self._upload_with_retry(local_file, remote_url, max_retries):
            print(f"[FTP] Upload failed for {basename}")
            sys.exit(1)  # stop script immediately
            return False

        # Download-back for verification
        if not self._download_with_retry(remote_url, local_verify, max_retries):
            print(f"[FTP] Download-back failed for {basename}")
            sys.exit(1)  # stop script immediately
            return False

        # Verify hash
        if sha256_file(local_file) != sha256_file(local_verify):
            print(f"[FTP] File mismatch after upload: {basename}")
            os.remove(local_verify)
            sys.exit(1)  # stop script immediately
            return False

        print(f"[FTP] Verified OK: {basename}")
        os.remove(local_verify)
        return True

    # -------------------------
    # Internal helpers
    # -------------------------
    def _upload_with_retry(self, local_file, remote_url, retries):
        for attempt in range(1, retries + 1):
            try:
                print(f"[FTP] Upload attempt {attempt}: {os.path.basename(local_file)}")
                with open(local_file, "rb") as f:
                    curl_upload.setopt(pycurl.URL, remote_url)
                    curl_upload.setopt(pycurl.UPLOAD, 1)
                    curl_upload.setopt(pycurl.READDATA, f)
                    curl_upload.perform()
                return True
            except pycurl.error as e:
                print(f"[FTP] Upload error (attempt {attempt}): {e}")
                time.sleep(2)
        return False

    def _download_with_retry(self, remote_url, local_file, retries):
        for attempt in range(1, retries + 1):
            try:
                print(f"[FTP] Download attempt {attempt}: {os.path.basename(local_file)}")
                with open(local_file, "wb") as f:
                    curl_download.setopt(pycurl.URL, remote_url)
                    curl_download.setopt(pycurl.WRITEFUNCTION, f.write)
                    curl_download.perform()
                return True
            except pycurl.error as e:
                print(f"[FTP] Download error (attempt {attempt}): {e}")
                time.sleep(2)
        return False

    def close(self):
        """Cleanup curl objects"""
        curl_upload.close()
        curl_download.close()
        print("[FTP] Curl sessions closed")
