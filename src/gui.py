# gui.py
import tkinter as tk
from tkinter import messagebox
import csv
import os
import threading
import webbrowser
from main import run_main as main_run  # import the callable main
import configs
from configs import PRODUCT_CSV

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "console_log.txt")

# -------------------------
# CSV Loader
# -------------------------
def load_products_from_csv():
    products = []
    try:
        with open(PRODUCT_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                products.append(row["PRODUCT"].strip())
    except FileNotFoundError:
        print(f"[WARN] {PRODUCT_CSV} not found. No products loaded.")
    return sorted(set(products))

# -------------------------
# Config Editor
# -------------------------
def open_config():
    if os.path.exists(PRODUCT_CSV):
        os.startfile(PRODUCT_CSV)
    else:
        messagebox.showerror("Error", f"{PRODUCT_CSV} not found!")

# =========================
# GUI
# =========================
root = tk.Tk()
root.title(f"Wafermap_Uploader v{configs.script_ver}")
root.geometry("350x400")

# Load products
products = load_products_from_csv()
selected_products = []

# -------------------------
# Product dropdown
# -------------------------
tk.Label(root, text="Select Product:").pack(anchor="w", padx=10)
var_product = tk.StringVar(value="")
dropdown = tk.OptionMenu(root, var_product, *products)
dropdown.pack(fill="x", padx=10, pady=(0, 10))

# -------------------------
# Listbox to show selected products
# -------------------------
mid_frame = tk.Frame(root)
mid_frame.pack(padx=10, pady=10, fill="both", expand=True)

# Buttons + / -
btn_frame = tk.Frame(mid_frame)
btn_frame.pack(side=tk.LEFT, padx=(0, 8))

def add_product():
    p = var_product.get()
    if not p:
        return
    if p not in selected_products:
        selected_products.append(p)
        listbox.insert(tk.END, p)

def remove_selected():
    for i in reversed(listbox.curselection()):
        selected_products.pop(i)
        listbox.delete(i)

tk.Button(btn_frame, text="➕", width=4, command=add_product).pack(pady=5)
tk.Button(btn_frame, text="➖", width=4, command=remove_selected).pack(pady=5)

# White listbox
listbox = tk.Listbox(mid_frame, selectmode=tk.MULTIPLE, height=8, bg="white")
listbox.pack(side=tk.LEFT, fill="both", expand=True)

# -------------------------
# Status bar
# -------------------------
status_var = tk.StringVar(value="Idle")
status_label = tk.Label(root, textvariable=status_var, anchor="w", fg="blue")
status_label.pack(fill="x", padx=10, pady=(0, 5))

# -------------------------
# Run main.py in thread
# -------------------------
def start_run():
    if not selected_products:
        messagebox.showerror("Error", "No product selected!")
        return

    run_btn.config(state="disabled")
    status_var.set("Running...")
    status_label.config(fg="orange")

    def target():
        import pythoncom
        import subprocess
        import sys
        try:
            pythoncom.CoInitialize()  # Initialize COM

            for product in selected_products:
                # Run main.py in a fresh Python process
                subprocess.run(
                    [sys.executable, os.path.join(BASE_DIR, "main.py"), product],
                    check=True
                )

            # When all products are done, update GUI
            root.after(0, on_run_complete)

        except subprocess.CalledProcessError as e:
            # Catch errors from subprocess (non-zero exit)
            err_msg = f"Error in product '{product}': {e}"
            root.after(0, lambda msg=err_msg: on_run_error(msg))
        except Exception as e:
            err_msg = str(e)
            root.after(0, lambda msg=err_msg: on_run_error(msg))
        finally:
            pythoncom.CoUninitialize()  # Clean up COM

    threading.Thread(target=target, daemon=True).start()

def on_run_complete():
    run_btn.config(state="normal")
    status_var.set("Completed")
    status_label.config(fg="green")
    messagebox.showinfo("Done", "Run completed.\nSee console_log.txt for details.")

def on_run_error(msg):
    run_btn.config(state="normal")
    status_var.set("Error")
    status_label.config(fg="red")
    messagebox.showerror("Run Failed", msg)

# -------------------------
# Buttons
# -------------------------
tk.Button(root, text="Edit Config (CSV)", command=open_config).pack(pady=5)

run_btn = tk.Button(
    root,
    text="RUN",
    bg="green",
    fg="white",
    width=25,
    command=start_run,
)
run_btn.pack(pady=10)

# -------------------------
# About Button
# -------------------------
def show_about():
    author = getattr(configs, "author", "Unknown")
    version = getattr(configs, "script_ver", "N/A")
    github_url = "https://github.com/juneth098/wafermap_uploader"

    about_win = tk.Toplevel(root)
    about_win.title("About wafermap_uploader")
    about_win.resizable(False, False)
    about_win.geometry("400x200")

    info_text = (
        f"wafermap_uploader\n"
        f"Version: {version}\n\n"
        f"Copyright (c) 2026 {author}\n"
        f"All rights reserved"
    )
    tk.Label(about_win, text=info_text, justify="left").pack(pady=(10,5), padx=10, anchor="w")

    def open_github(event):
        webbrowser.open_new(github_url)

    link = tk.Label(about_win, text=github_url, fg="blue", cursor="hand2")
    link.pack(pady=(5,10), padx=10, anchor="w")
    link.bind("<Button-1>", open_github)

    tk.Button(about_win, text="Close", command=about_win.destroy).pack(pady=10)

about_btn = tk.Button(root, text="About", command=show_about)
about_btn.pack(pady=5)

# -------------------------
# Start GUI loop
# -------------------------
root.mainloop()
