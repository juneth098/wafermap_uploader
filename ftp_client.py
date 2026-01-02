# ftp_client.py
from ftplib import FTP
import os
import pycurl
import time

class FTPClient:
    def __init__(self, base_url, userpwd, remote_dir="/"):
        self.base_url = base_url
        self.user, self.pwd = userpwd.split(":", 1)
        self.remote_dir = remote_dir

    def upload(self, local_file):
        filename = os.path.basename(local_file)
        try:
            with FTP(self.base_url) as ftp:
                ftp.login(self.user, self.pwd)

                # Ensure remote directory exists (change to it)
                ftp.cwd(self.remote_dir)

                with open(local_file, "rb") as f:
                    ftp.storbinary(f"STOR {filename}", f)

            print(f"[FTP] Uploaded {filename} to {self.remote_dir}")
        except Exception as e:
            print(f"[ERROR] FTP upload failed for {local_file}: {e}")

def upload_with_retry(curl, local_file, remote_url, retries=3):
    for attempt in range(1, retries + 1):
        try:
            print(f"[FTP] Upload attempt {attempt}: {os.path.basename(local_file)}")

            with open(local_file, "rb") as f:
                curl.setopt(pycurl.URL, remote_url)
                curl.setopt(pycurl.UPLOAD, 1)
                curl.setopt(pycurl.READDATA, f)
                curl.perform()

            return True
        except pycurl.error as e:
            print(f"[ERROR] Upload failed (attempt {attempt}): {e}")
            time.sleep(2)

def download_with_retry(curl, remote_url, local_file, retries=3):
    for attempt in range(1, retries + 1):
        try:
            print(f"[FTP] Download attempt {attempt}: {os.path.basename(local_file)}")

            with open(local_file, "wb") as f:
                curl.setopt(pycurl.URL, remote_url)
                curl.setopt(pycurl.WRITEFUNCTION, f.write)
                curl.perform()

            return True
        except pycurl.error as e:
            print(f"[ERROR] Download failed (attempt {attempt}): {e}")
            time.sleep(2)

    return False