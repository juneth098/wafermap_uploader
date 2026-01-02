# mailer.py
import win32com.client
import os
from datetime import datetime

# Prepare stats for email
to_list = ["juneth.viktor@ftdichip.com."]  # replace with actual recipients
#to_list = ["ftdi_prodtest@ftdichip.com."]  # replace with actual recipients
#cc_list = ["manager@example.com"]  # optional
#attachments = []  # optional, add file paths if needed


def send_completion_mail(
    product,
    total_wafers,
    uploaded_wafers,
    ftp_dir,
    to_list,
    cc_list=None,
    attachments=None
):
    """
    Send completion notification via Outlook
    """

    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)  # MailItem

    mail.Subject = f"GTK → UMC Upload Completed | {product}"

    mail.Body = f"""
GTK to UMC processing completed successfully.

Product       : {product}
Total wafers  : {total_wafers}
Uploaded      : {uploaded_wafers}
FTP Directory : {ftp_dir}
Upload Agent  : gtk_to_umc
Timestamp     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is an automated message.
"""

    mail.To = ";".join(to_list)

    if cc_list:
        mail.CC = ";".join(cc_list)

    if attachments:
        for file in attachments:
            if file and os.path.exists(file):
                mail.Attachments.Add(file)

    mail.Send()
    print("[MAIL] Outlook notification sent")