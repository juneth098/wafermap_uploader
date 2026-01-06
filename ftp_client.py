# ftp_client.py
from ftplib import FTP
import os
import time

MAX_FTP_RETRIES = 3  # default max retries

class FTPClient:
    def __init__(self, url, userpwd):
        """
        Initialize FTP connection.
        url: FTP server address
        userpwd: "username:password"
        """
        self.url = url
        self.user, self.pwd = userpwd.split(":")
        print(f"[FTP] Connecting to {self.url} ...")
        self.ftp = FTP(self.url)
        self.ftp.login(self.user, self.pwd)
        print(f"[FTP] Logged in as {self.user}")

    def upload_and_verify(self, filepath, remote_dir=None, max_retries=MAX_FTP_RETRIES):
        """
        Upload a file to FTP server with retries.
        filepath: full local path
        remote_dir: FTP directory to upload to (optional)
        """
        filename = os.path.basename(filepath)

        for attempt in range(1, max_retries + 1):
            print(f"[FTP] Upload attempt {attempt}: {filename}")
            try:
                # open file for each retry to avoid "read of closed file"
                with open(filepath, "rb") as f:
                    if remote_dir:
                        self._ensure_dir(remote_dir)
                        self._safe_cwd(remote_dir)
                    self.ftp.storbinary(f"STOR {filename}", f)

                # verify file exists on server
                try:
                    files = self.ftp.nlst(remote_dir or ".")
                except Exception:
                    files = []
                if filename in files:
                    print(f"[FTP] Upload successful: {filename}")
                    return True
                else:
                    print(f"[FTP] Upload incomplete, retrying...")
                    time.sleep(1)

            except Exception as e:
                print(f"[FTP] ERROR: Upload failed (attempt {attempt}): {e}")
                time.sleep(1)

        print(f"[FTP] FAILED to upload after {max_retries} attempts: {filename}")
        return False

    def _ensure_dir(self, path):
        """Create remote directory if it doesn't exist"""
        dirs = path.strip("/").split("/")
        for d in dirs:
            try:
                if d not in self.ftp.nlst():
                    try:
                        self.ftp.mkd(d)
                        print(f"[FTP] Created directory: {d}")
                    except Exception:
                        print(f"[FTP] WARNING: Failed to create directory '{d}' (may already exist or permission issue)")
                self._safe_cwd(d)
            except Exception as e:
                print(f"[FTP] WARNING: Cannot enter directory '{d}': {e}")

    def _safe_cwd(self, path):
        """Change to directory safely"""
        try:
            self.ftp.cwd(path)
        except Exception as e:
            print(f"[FTP] WARNING: Failed to change directory to '{path}': {e}")

    def close(self):
        """Close FTP connection"""
        if self.ftp:
            try:
                self.ftp.quit()
                print("[FTP] Connection closed")
            except Exception as e:
                print(f"[FTP] WARNING: Failed to close FTP connection: {e}")
