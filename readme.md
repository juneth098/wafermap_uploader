# ![WaferMapUploader](./bin/wafermap_uploader.ico) WaferMap Uploader

[![License](https://img.shields.io/github/license/juneth098/wafermap_uploader)](LICENSE)

**WaferMap Uploader** is a desktop utility that **converts wafer maps provided by OSATs and transforms them into the foundry’s UMC format**, and then **uploads the converted files to an FTP server**.

This tool simplifies wafer map processing and automates upload workflows for semiconductor test data handling.

---

## 🔹 Features

- 📥 Accepts raw wafer map inputs from OSAT
- 🔄 Converts wafer maps into the **UMC-compatible format**
- 📤 Supports **FTP upload** to remote server
- Updates **PHPMyAdmin database** for successfully uploaded wafers
- 🖥️ Includes a **GUI interface** (`gui.py`) for easy file selection and processing
- 📫 Optional email notification on upload completion

---

## 💾 Download EXE

The latest Windows executable can be downloaded from the **GitHub Releases** page:

[Download WaferMapUploader EXE](https://github.com/juneth098/wafermap_uploader/releases/latest)  

- **Single-file EXE** (no console window)  
- Includes the app icon located at `./bin/wafermap_uploader.ico`  
- **No Python installation required**

---

## 🚀 Quickstart

### Using the EXE

1. Download and **run `WaferMapUploader.exe`**.
2. **Select Input Wafer Map**  
   - Click **Browse** and choose the raw wafer map file from OSAT.
3. **Set Output Options**  
   - Confirm or set UMC output format (naming, directories, etc.).
4. **Configure FTP Upload**  
   - Enter FTP **host**, **username**, **password**, and **remote path**.  
   - Optionally, test the connection.
5. **Convert & Upload**  
   - Click **Convert** to generate the UMC file.  
   - Click **Upload** to send the file to the FTP server.
6. **Optional Email Notification**  
   - Configure email settings to notify upon upload completion.

### Using the Python GUI (if running from source)

1. Install Python 3.10+  
2. Run `src/gui.py` directly:
```bash 

