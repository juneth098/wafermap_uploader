# mailer.py
from enum import unique

import win32com.client
import os
from datetime import datetime

# Prepare stats for email
to_list=[]
to_list.append("juneth.viktor@ftdichip.com")  # For test environment
#to_list.append("alamuri.venkateswararao@ftdichip.com")  # For test environment
#to_list.append("ftdi_prodtest@ftdichip.com")  # replace with actual recipients
#cc_list = ["manager@example.com"]  # optional
#attachments = []  # optional, add file paths if needed


def send_completion_mail(
    product,
    lots,
    total_wafers,
    uploaded_wafers,
    db_update_count,
    ftp_dir,
    to_list,
    cc_list=None,
    attachments=None
):
    #remove duplicates
    unique_lot = list(dict.fromkeys(lots))

    """
    Send completion notification via Outlook
    """

    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)  # MailItem

    mail.Subject = f"GTK → UMC Upload Completed | {product}"

    mail.Body = f"""
GTK to UMC processing completed successfully.

Product\t\t\t\t: {product}
Lot ID\t\t\t\t: {", ".join(unique_lot)}
Total wafers\t\t\t\t: {total_wafers}
FTP: Uploaded Map\t\t\t\t: {uploaded_wafers}
DB: Updated Rows\t\t\t\t: {db_update_count}
FTP Directory\t\t\t\t: {ftp_dir}
Upload Agent\t\t\t\t: gtk_to_umc
Timestamp\t\t\t\t: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is an automated message.
"""

    mail.To = ";".join(to_list)

    if cc_list:
        mail.CC = ";".join(cc_list)

    if attachments:
        for file in attachments:
            if file and os.path.exists(file):
                mail.Attachments.Add(file)

    print(f"{mail.Body}")
    mail.Send()
    print("[MAIL] Outlook notification sent")

