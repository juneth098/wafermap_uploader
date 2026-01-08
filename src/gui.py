import tkinter as tk
from tkinter import messagebox
import csv
import subprocess
import sys
import os
import threading
import configs
import webbrowser

PRODUCT_CSV = "product_config.csv"
LOG_FILE = "../console_log.txt"


# -------------------------
# CSV Loader
# -------------------------
def load_products_from_csv():
    products = []
    with open(PRODUCT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            products.append(row["PRODUCT"].strip())
    return sorted(set(products))


# -------------------------
# Config Editor
# -------------------------
def open_config():
    os.startfile(PRODUCT_CSV)


# -------------------------
# Run main.py (background)
# -------------------------
def start_run():
    if not selected_products:
        messagebox.showerror("Error", "No product selected")
        return

    run_btn.config(state="disabled")
    status_var.set("Running...")
    status_label.config(fg="orange")

    t = threading.Thread(target=run_main, daemon=True)
    t.start()

def run_main(selected_products):
    global process

    if not selected_products:
        messagebox.showerror("Error", "No product selected")
        return

    run_btn.config(state="disabled")
    status_var.set("Starting...")

    with open(LOG_FILE, "w") as log:
        process = subprocess.Popen(
            [
                sys.executable,
                "main.py",
                ",".join(selected_products)
            ],
            stdout=log,
            stderr=subprocess.STDOUT,
        )

    root.after(500, monitor_progress)

def monitor_progress():
    global process

    if not process:
        return

    try:
        with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            # Scan for error messages first
            error_lines = [l for l in lines if "[ERROR]" in l or "Traceback" in l]
            if error_lines:
                status_var.set(error_lines[-1].strip())  # show last error
                run_btn.config(state="normal")
                process = None
                return

            # Otherwise show progress like x/y
            for line in reversed(lines):
                if "/" in line:
                    status_var.set(line.strip())
                    break
    except Exception:
        pass

    # Still running?
    if process and process.poll() is None:
        root.after(500, monitor_progress)
    elif process:
        # finished without errors
        status_var.set("Completed")
        run_btn.config(state="normal")
        process = None
        #messagebox.showinfo("Done", "Run completed.\nSee console_log.txt")
def on_run_complete():
    run_btn.config(state="normal")
    status_var.set("Completed")
    status_label.config(fg="green")
    #show_log_popup()


def on_run_error(msg):
    run_btn.config(state="normal")
    status_var.set("Error")
    status_label.config(fg="red")
    messagebox.showerror("Run Failed", msg)


# -------------------------
# Log popup (after finish)
# -------------------------
def show_log_popup():
    win = tk.Toplevel(root)
    win.title("Console Logs")
    win.geometry("800x450")

    text = tk.Text(win, wrap="word")
    text.pack(fill="both", expand=True)

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            text.insert("1.0", f.read())
    except Exception as e:
        text.insert("1.0", f"Failed to load log:\n{e}")

    text.config(state="disabled")


# =========================
# GUI
# =========================
root = tk.Tk()
root.title(f"Wafermap_Uploader v{configs.script_ver}")
root.geometry("300x350")

products = load_products_from_csv()
selected_products = []

# Product dropdown
tk.Label(root, text="Product").pack(anchor="w", padx=10)

var_product = tk.StringVar(value="")
dropdown = tk.OptionMenu(root, var_product, *products)
dropdown.pack(fill="x", padx=10, pady=(0, 10))


# -------------------------
# Add / Remove logic
# -------------------------
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

# -------------------- About window --------------------
def show_about():
    try:
        author = configs.author
        version = configs.script_ver
    except AttributeError:
        author = "Unknown"
        version = "N/A"
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
    tk.Label(about_win, text=info_text, justify="left").pack(pady=(10, 5), padx=10, anchor="w")
    def open_github(event):
        webbrowser.open_new(github_url)
    link = tk.Label(about_win, text=github_url, fg="blue", cursor="hand2")
    link.pack(pady=(5, 10), padx=10, anchor="w")
    link.bind("<Button-1>", open_github)
    tk.Button(about_win, text="Close", command=about_win.destroy).pack(pady=10)


# Middle layout
mid_frame = tk.Frame(root)
mid_frame.pack(padx=10, pady=10, fill="both", expand=True)

# Left buttons (+ / -)
btn_frame = tk.Frame(mid_frame)
btn_frame.pack(side=tk.LEFT, padx=(0, 8))

tk.Button(btn_frame, text="+", width=4, command=add_product).pack(pady=5)
tk.Button(btn_frame, text="-", width=4, command=remove_selected).pack(pady=5)

# White listbox
listbox = tk.Listbox(
    mid_frame,
    selectmode=tk.MULTIPLE,
    height=8,
    bg="white"
)
listbox.pack(side=tk.LEFT, fill="both", expand=True)




# -------------------------
# Bottom buttons
# -------------------------
tk.Button(root, text="Edit Config (CSV)", command=open_config).pack(pady=5)

run_btn = tk.Button(
    root,
    text="RUN",
    bg="green",
    fg="white",
    width=20,
    command=lambda: run_main(selected_products),
)
run_btn.pack(pady=10)


# -------------------- Add About Button --------------------
about_btn = tk.Button(root, text="About", command=show_about)
about_btn.pack(pady=5)

# -------------------------
# Status bar
# -------------------------
status_var = tk.StringVar(value="Idle")

status_label = tk.Label(
    root,
    textvariable=status_var,
    anchor="w",
    fg="blue"
)
status_label.pack(fill="x", padx=10, pady=(0, 5))

root.mainloop()
