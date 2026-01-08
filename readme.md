# ![WaferMapUploader](./bin/wafermap_uploader.ico) WaferMap Uploader

[![License](https://img.shields.io/github/license/juneth098/wafermap_uploader)](LICENSE)

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

## 💾 Download EXE

The latest Windows executable can be downloaded from the **GitHub Releases** page:

[Download WaferMapUploader EXE](https://github.com/juneth098/wafermap_uploader/releases/latest)  

- **Single-file EXE** (no console window)
- **No Python installation required**




---

## 🚀 Quickstart

### Using the EXE

1. **Download and run `WaferMapUploader.exe`.**  
2. **Choose product/s** and click **➕ button**.  
3. **Remove product/s** by clicking the **➖ button**.  
4. **(Optional) Update configurations** by clicking the **“Configs” button**:  
   - Configure fields such as `PRODUCT`, `DEVICE_NAME`, `SUBCON`, `TESTER`, `TEST_PROGRAM`, `LOAD_BOARD`, `PROBE_CARD`, `SOFT_BINS`.  
5. **Click “Run”** to process the wafer maps:  
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
2. Run `src/gui.py` directly:
```bash 
python src/gui.py 
```
3. **Choose product/s** and click **➕ button**.  
4. **Remove product/s** by clicking the **➖ button**. 
5. **(Optional) Update configurations** by clicking the **“Edit Config (CSV)” button**:  
   - Configure fields such as `PRODUCT`, `DEVICE_NAME`, `SUBCON`, `TESTER`, `TEST_PROGRAM`, `LOAD_BOARD`, `PROBE_CARD`, `SOFT_BINS`.  
6. **Click “Run”** to process the wafer maps:  
   - Converts the wafer maps into **UMC standard format**.  
   - Uploads the converted files to the **FTP server**.  
   - Updates the **status in the database**.   
   - Sends an email notification upon successful upload.

## 🗂️ Project Structure

````
wafermap_uploader/
├── raw_wafer_map/         # Example raw wafer maps
├── src/
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
Copyright (c) 2026 Juneth Viktor Ellon Moreno
All rights reserved.
````
This project is closed‑source unless otherwise declared.

## 📝 Author

**Juneth Viktor Ellon Moreno**

- LinkedIn: [https://www.linkedin.com/in/junethmoreno/](https://www.linkedin.com/in/junethmoreno/)  
- GitHub: [https://github.com/juneth098/](https://github.com/juneth098/)


## 💬 Support 
For issues, enhancements, or questions, please contact the author or open an issue in the repository.