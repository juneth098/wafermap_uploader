# ftp_client.py
import os
import time
import pycurl
from utils import sha256_file
from configs import FTP_USERPWD
import sys

MAX_FTP_RETRIES = 3




class FTPClient:
    """
    FTP client using pycurl for upload + verification
    """

    def __init__(self, ftp_base_url, remote_dir="/"):
        self.ftp_base_url = ftp_base_url.rstrip("/")
        self.remote_dir = remote_dir

        # -------------------------
        # Create reusable curl objects for upload/download
        # -------------------------
        self.curl_upload = pycurl.Curl()
        self.curl_upload.setopt(pycurl.USERPWD, FTP_USERPWD)
        self.curl_upload.setopt(pycurl.VERBOSE, 0)

        self.curl_download = pycurl.Curl()
        self.curl_download.setopt(pycurl.USERPWD, FTP_USERPWD)
        self.curl_download.setopt(pycurl.VERBOSE, 0)

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
                    self.curl_upload.setopt(pycurl.URL, remote_url)
                    self.curl_upload.setopt(pycurl.UPLOAD, 1)
                    self.curl_upload.setopt(pycurl.READDATA, f)
                    self.curl_upload.perform()
                return True
            except pycurl.error as e:
                print(f"[FTP] Upload error (attempt {attempt}): {e}")
                time.sleep(2)
                # Reset handle for retry
                self._reset_upload_handle()
        return False

    def _download_with_retry(self, remote_url, local_file, retries):
        for attempt in range(1, retries + 1):
            try:
                print(f"[FTP] Download attempt {attempt}: {os.path.basename(local_file)}")
                with open(local_file, "wb") as f:
                    self.curl_download.setopt(pycurl.URL, remote_url)
                    self.curl_download.setopt(pycurl.WRITEFUNCTION, f.write)
                    self.curl_download.perform()
                return True
            except pycurl.error as e:
                print(f"[FTP] Download error (attempt {attempt}): {e}")
                time.sleep(2)
                # Reset handle for retry
                self._reset_download_handle()
        return False
    # -------------------------
    # Reset handles on failure
    # -------------------------
    def _reset_upload_handle(self):
        self.curl_upload.close()
        self.curl_upload = pycurl.Curl()
        self.curl_upload.setopt(pycurl.USERPWD, FTP_USERPWD)
        self.curl_upload.setopt(pycurl.VERBOSE, 0)

    def _reset_download_handle(self):
        self.curl_download.close()
        self.curl_download = pycurl.Curl()
        self.curl_download.setopt(pycurl.USERPWD, FTP_USERPWD)
        self.curl_download.setopt(pycurl.VERBOSE, 0)

    def close(self):
        """Cleanup curl objects"""
        self.curl_upload.close()
        self.curl_download.close()
        print("[FTP] Curl sessions closed")
