# mailer.py
import win32com.client
import os
from datetime import datetime
from utils import diff_file
import sys
# Make sure it's an absolute path
diff_file_path = os.path.join(os.getcwd(), diff_file)  # or use your TEMP_DL_DIR if

# Prepare stats for email
to_list=[]
to_list.append("juneth.viktor@ftdichip.com")  # For test environment
#to_list.append("alamuri.venkateswararao@ftdichip.com")  # For test environment
#to_list.append("ftdi_prodtest@ftdichip.com")  # replace with actual recipients
#cc_list = ["manager@example.com"]  # optional
attachments = []  # optional, add file paths if needed


def send_completion_mail(
    product,
    lots,
    total_wafers,
    uploaded_wafers,
    db_update_count,
    ftp_dir,
    to_list,
    cc_list=None,
    attachments=diff_file_path,
    error=0,
    has_attach=False,
):
    #remove duplicates
    unique_lot = list(dict.fromkeys(lots))

    """
    Send completion notification via Outlook
    """

    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)  # MailItem


    if error == 0:
        mail.Subject = f"GTK → UMC Upload Completed | {product}"
        mail.HTMLBody = f"""
        <html>
        <body style="font-family:Calibri; font-size:11pt;">
        <h3>GTK to UMC processing completed successfully</h3>
    
        <table cellpadding="4">
        <tr><td><b>Product</b></td><td>:</td><td>{product}</td></tr>
        <tr><td><b>Lot ID</b></td><td>:</td><td>{", ".join(unique_lot)}</td></tr>
        <tr><td><b>Total wafers</b></td><td>:</td><td>{total_wafers}</td></tr>
        <tr><td><b>FTP: Uploaded Map</b></td><td>:</td><td>{uploaded_wafers}</td></tr>
        <tr><td><b>DB: Updated Rows</b></td><td>:</td><td>{db_update_count}</td></tr>
        <tr><td><b>FTP Directory</b></td><td>:</td><td>{ftp_dir}</td></tr>
        <tr><td><b>Upload Agent</b></td><td>:</td><td>gtk_to_umc</td></tr>
        <tr><td><b>Timestamp</b></td><td>:</td><td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
        </table>
    
        <p>This is an automated message.</p>
        </body>
        </html>
        """

    if error !=0: #error found
        mail.Subject = f"GTK → UMC Upload FAIL | {product}"
        mail.HTMLBody = f"""
        <html>
        <body style="font-family:Calibri; font-size:11pt;">
         <h3 style="color:red;">GTK to UMC encountered {error} error/s</h3>

        <table cellpadding="4">
        <tr><td><b>Product</b></td><td>:</td><td>{product}</td></tr>
        <tr><td><b>Lot ID</b></td><td>:</td><td>{", ".join(unique_lot)}</td></tr>
        <tr><td><b>Total wafers</b></td><td>:</td><td>{total_wafers}</td></tr>
        <tr><td><b>FTP: Uploaded Map</b></td><td>:</td><td>{uploaded_wafers}</td></tr>
        <tr><td><b>DB: Updated Rows</b></td><td>:</td><td>{db_update_count}</td></tr>
        <tr><td><b>FTP Directory</b></td><td>:</td><td>{ftp_dir}</td></tr>
        <tr><td><b>Upload Agent</b></td><td>:</td><td>gtk_to_umc</td></tr>
        <tr><td><b>Timestamp</b></td><td>:</td><td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
        </table>

        <p>This is an automated message.</p>
        </body>
        </html>
        """

    if total_wafers ==0: #0 wafers
        mail.Subject = f"GTK → UMC Nothing to upload | {product}"
        mail.HTMLBody = f"""
        <html>
        <body style="font-family:Calibri; font-size:11pt;">
         <h3 style="color:gray;">Nothing to upload</h3>

        <table cellpadding="4">
        <tr><td><b>Product</b></td><td>:</td><td>{product}</td></tr>
        <tr><td><b>Lot ID</b></td><td>:</td><td>{", ".join(unique_lot)}</td></tr>
        <tr><td><b>Total wafers</b></td><td>:</td><td>{total_wafers}</td></tr>
        <tr><td><b>FTP: Uploaded Map</b></td><td>:</td><td>{uploaded_wafers}</td></tr>
        <tr><td><b>DB: Updated Rows</b></td><td>:</td><td>{db_update_count}</td></tr>
        <tr><td><b>FTP Directory</b></td><td>:</td><td>{ftp_dir}</td></tr>
        <tr><td><b>Upload Agent</b></td><td>:</td><td>gtk_to_umc</td></tr>
        <tr><td><b>Timestamp</b></td><td>:</td><td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
        </table>

        <p>This is an automated message.</p>
        </body>
        </html>
        """

    mail.To = ";".join(to_list)

    if cc_list:
        mail.CC = ";".join(cc_list)

    if attachments and has_attach:
        # Ensure attachments is always a list
        if isinstance(attachments, str):
            attachments = [attachments]

        for file in attachments:
            if file:
                if os.path.exists(file):
                    print(f"[MAIL] Attaching file: {file}")
                    mail.Attachments.Add(file)
                else:
                    print(f"[MAIL] WARNING: Attachment not found or missing: {file}")
                    sys.exit(1)  # stop script immediately

    print(f"{mail.Body}")
    mail.Send()
    print("[MAIL] Outlook notification sent")

