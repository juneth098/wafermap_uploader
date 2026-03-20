# ![WaferMapUploader](./bin/wafermap_uploader.ico) WaferMap Uploader

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**WaferMap Uploader** is a desktop utility that **converts wafer maps provided by OSATs and transforms them into the foundry’s UMC format**, and then **uploads the converted files to an FTP server**.

This tool simplifies wafer map processing and automates upload workflows for semiconductor test data handling.

---

## 🔹 Features

- 🗂️ Accepts raw wafer map inputs from OSAT
- ⚙️ Converts wafer maps into the UMC-compatible format
- 📤 Supports FTP upload to remote server
- 🗃️ Updates PHPMyAdmin database for successfully uploaded wafers
- 🖥️ Includes a GUI interface (gui.py) for easy file selection and processing
- ✉️  email notification on upload completion

---


## 🔹 Supported Products

- FT4232H-C 
- FT233H-B   
- FT260-B   
- FT4233H-C  
- FT232RV2-C
- FT4232HA
- FT4232HAN

---

## 💾 Download ZIP

The latest Zip can be downloaded from the **GitHub Releases** page:

[Download WaferMapUploader EXE](https://github.com/juneth098/wafermap_uploader/releases/latest)  

````
WaferMapUploader.zip
└── WafermapUploader.exe        # Executable file
`````




---

## 🚀 Quickstart

### Using the EXE

1. **Download  and extract the zip file**
2. Create .env file containing FTP and DB access:
   - check with Admin for credentials
   
EXAMPLE ONLY:
````
#DB Access
DB_URI=mysql://abc123:AbCD1234@10.10.0.10
#FTP Access
FTP_USERPWD=user:password@abc123
````
3. **Run `WaferMapUploader.exe`.**  
4. Click `Select Product` dropdown and choose product then click **➕ button** to add.  
5. **To Remove**, Highlight product in the `listbox` then click  **➖ button**.
6. **Click `Run`** to process the wafer maps:  
   - Converts the wafer maps into **UMC standard format**.  
   - Uploads the converted files to the **FTP server**.  
   - Updates the **status in the database**.   
   - Sends an email notification upon successful upload.


### (Optional) Download the Git repository

Clone the repository to your local machine:

```bash
git clone https://github.com/juneth098/wafermap_uploader.git
```

### Using the Python GUI (if running from source)

1. Install Python 3.10+ 
2. Create .env file containing FTP and DB access:
   - check with Admin for credentials


   EXAMPLE ONLY:
````
#DB Access
DB_URI=mysql://abc123:AbCD1234@10.10.0.10
#FTP Access
FTP_USERPWD=user:password@abc123
````
3. Run `src/gui.py` directly:
```bash 
python src/gui.py 
```
4. Click `Select Product` dropdown and choose product then click **➕ button** to add.  
5. **To Remove**, Highlight product in the `listbox` then click  **➖ button**.  
6. **Click `Run`** to process the wafer maps:  
   - Converts the wafer maps into **UMC standard format**.  
   - Uploads the converted files to the **FTP server**.  
   - Updates the **status in the database**.   
   - Sends an email notification upon successful upload.

## 🗂️ Project Structure

````
wafermap_uploader/
├── raw_wafer_map/         # Example raw wafer maps
├── src/
│   ├── .env                # Created by USER
│   ├── product_configs.csv # Product Configurations
│   ├── gui.py              # Main GUI interface
│   ├── main.py             # Entry script
│   ├── configs.py          # Config loader
│   ├── db.py               # Database helpers
│   ├── ftp_client.py       # FTP upload logic
│   ├── mailer.py           # Optional email notification
│   ├── scanner.py          # File scanning utilities
│   ├── umc_writer.py       # UMC conversion logic
│   └── utils.py            # Helpers
├── bin/
│   └── wafermap_uploader.ico
└── .github/
    └── workflows/
        └── build-exe.yml

`````
## 🛠️ License
````
MIT License

Copyright (c) 2026 Juneth Viktor Ellon Moreno
````
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

## 📝 Author

**Juneth Viktor Ellon Moreno**

- LinkedIn: [https://www.linkedin.com/in/junethmoreno/](https://www.linkedin.com/in/junethmoreno/)  
- GitHub: [https://github.com/juneth098/](https://github.com/juneth098/)


## 💬 Support 
For issues, enhancements, or questions, please contact the author or open an issue in the repository.