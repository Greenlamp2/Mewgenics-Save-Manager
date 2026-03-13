import os
import sys
import shutil
import random
import threading
import tkinter as tk

APP_VERSION = "1.0.6"
from tkinter import simpledialog, messagebox
from datetime import datetime
import keyboard
import pygame

# Resolve base path (handles PyInstaller bundling)
def _base_path():
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

FX_FART_FOLDER = os.path.join(_base_path(), "fx", "fart")
FX_BURP_FOLDER = os.path.join(_base_path(), "fx", "burp")

# Initialize pygame mixer once at startup
pygame.mixer.init()

def _play_sound(path):
    """Play a sound file in a background thread (non-blocking)."""
    def _run():
        try:
            sound = pygame.mixer.Sound(path)
            sound.play()
        except Exception as e:
            print(f"[sound] Error playing {path}: {e}")
    threading.Thread(target=_run, daemon=True).start()


USER_HOME = os.path.expanduser("~")
APPDATA = os.getenv("APPDATA")

def detect_steam_save_folder():

    appdata = os.getenv("APPDATA")

    mewgenics_root = os.path.join(
        appdata,
        "Glaiel Games",
        "Mewgenics"
    )

    if not os.path.exists(mewgenics_root):
        return None

    for folder in os.listdir(mewgenics_root):

        path = os.path.join(mewgenics_root, folder)

        if folder.isdigit():

            saves_path = os.path.join(path, "saves")

            if os.path.exists(saves_path):
                return saves_path

    return None

WATCH_FOLDER = detect_steam_save_folder()

TARGET_FILE = "steamcampaign01.sav"
TARGET_PATH = os.path.join(WATCH_FOLDER, TARGET_FILE)

CUSTOM_FOLDER = os.path.join(WATCH_FOLDER, "custom")

SPECIAL_BACKUP_FOLDER = os.path.join(CUSTOM_FOLDER, "named_backups")
SAFETY_FOLDER = os.path.join(CUSTOM_FOLDER, "restore_safety")

os.makedirs(SPECIAL_BACKUP_FOLDER, exist_ok=True)
os.makedirs(SAFETY_FOLDER, exist_ok=True)


def create_restore_safety_backup():

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safety_name = f"safety_{timestamp}.sav"
    safety_path = os.path.join(SAFETY_FOLDER, safety_name)

    shutil.copy2(TARGET_PATH, safety_path)

    print(f"🛟 Safety backup created: {safety_name}")


class SaveManagerUI:

    def __init__(self, root):

        self.root = root

        root.title("Mewgenics Save Manager")
        root.geometry("320x400")
        root.attributes("-topmost", True)


        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)

        self.save_button = tk.Button(
            button_frame,
            text="Save Backup",
            height=2,
            command=self.create_named_backup
        )

        self.save_button.pack(side="left", padx=5)

        self.quick_save_button = tk.Button(
            button_frame,
            text="Quick Save (F7)",
            height=2,
            command=self.create_quick_save
        )

        self.quick_save_button.pack(side="left", padx=5)

        self.quick_load_button = tk.Button(
            button_frame,
            text="Quick Load (F9)",
            height=2,
            command=self.quick_load
        )

        self.quick_load_button.pack(side="left", padx=5)

        self.listbox = tk.Listbox(root)

        self.listbox.pack(fill="both", expand=True, padx=10)

        self.listbox.bind("<Double-Button-1>", lambda e: self.reload_backup())

        # Global hotkeys (work even when the app is not focused)
        keyboard.add_hotkey("F7", lambda: root.after(0, self.create_quick_save))
        keyboard.add_hotkey("F9", lambda: root.after(0, lambda: self.quick_load(confirm=False)))

        action_frame = tk.Frame(root)
        action_frame.pack(pady=5)

        self.reload_button = tk.Button(
            action_frame,
            text="Reload Selected",
            command=self.reload_backup
        )

        self.reload_button.pack(side="left", padx=5)

        self.delete_button = tk.Button(
            action_frame,
            text="Clean Backups (keep 5)",
            command=self.clean_backups
        )

        self.delete_button.pack(side="left", padx=5)

        bottom_frame = tk.Frame(root)
        bottom_frame.pack(fill="x", padx=10, pady=(5, 5))

        self.topmost_var = tk.BooleanVar(value=True)
        self.topmost_check = tk.Checkbutton(
            bottom_frame,
            text="Always on top",
            variable=self.topmost_var,
            command=self.toggle_topmost
        )
        self.topmost_check.pack(side="left")

        self.mute_var = tk.BooleanVar(value=False)
        self.mute_check = tk.Checkbutton(
            bottom_frame,
            text="Mute",
            variable=self.mute_var
        )
        self.mute_check.pack(side="left", padx=(10, 0))

        self.version_label = tk.Label(bottom_frame, text=f"v{APP_VERSION}", fg="gray", font=("Arial", 8))
        self.version_label.pack(side="right")

        self.refresh_list()


    def toggle_topmost(self):
        self.root.attributes("-topmost", self.topmost_var.get())

    def refresh_list(self):

        self.listbox.delete(0, tk.END)

        folders = [
            f for f in os.listdir(SPECIAL_BACKUP_FOLDER)
            if os.path.isdir(os.path.join(SPECIAL_BACKUP_FOLDER, f))
        ]

        folders.sort(
            key=lambda f: os.path.getctime(os.path.join(SPECIAL_BACKUP_FOLDER, f)),
            reverse=True
        )

        for f in folders:
            path = os.path.join(SPECIAL_BACKUP_FOLDER, f)

            creation_time = os.path.getctime(path)

            date_str = datetime.fromtimestamp(creation_time).strftime("%d/%m/%y %H:%M:%S")

            display = f"{date_str}   {f}"

            self.listbox.insert(tk.END, display)

    def quick_load(self, confirm=True):

        if self.listbox.size() == 0:
            messagebox.showinfo("Quick Load", "No backup available")
            return

        entry = self.listbox.get(0)
        name = entry.split("   ", 1)[1]

        folder = os.path.join(SPECIAL_BACKUP_FOLDER, name)
        backup_file = os.path.join(folder, TARGET_FILE)

        if not os.path.exists(backup_file):
            messagebox.showerror("Error", "Backup file missing")
            return

        if confirm:
            answer = messagebox.askyesno(
                "Quick Load",
                f"Load most recent backup '{name}' ?"
            )
            if not answer:
                return

        create_restore_safety_backup()

        try:
            shutil.copy2(backup_file, TARGET_PATH)
            if not self.mute_var.get():
                burps = [
                    os.path.join(FX_BURP_FOLDER, f)
                    for f in os.listdir(FX_BURP_FOLDER)
                    if f.lower().endswith(".mp3")
                ]
                if burps:
                    _play_sound(random.choice(burps))
            print(f"⚡ Quick loaded: {name}")
        except Exception as e:
            messagebox.showerror("Quick Load Error", str(e))
            print(f"❌ Quick load failed: {e}")

    def create_quick_save(self):

        name = f"quicksave_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        folder_path = os.path.join(SPECIAL_BACKUP_FOLDER, name)

        try:
            os.makedirs(folder_path)
            shutil.copy2(TARGET_PATH, os.path.join(folder_path, TARGET_FILE))
            print(f"⚡ Quick save created: {name}")
            if not self.mute_var.get():
                farts = [
                    os.path.join(FX_FART_FOLDER, f)
                    for f in os.listdir(FX_FART_FOLDER)
                    if f.lower().endswith(".mp3")
                ]
                if farts:
                    _play_sound(random.choice(farts))
        except Exception as e:
            messagebox.showerror("Quick Save Error", str(e))
            print(f"❌ Quick save failed: {e}")

        self.refresh_list()

    def create_named_backup(self):

        name = simpledialog.askstring(
            "Backup Name",
            "Enter backup name:"
        )

        if not name:
            return

        safe_name = name.replace(" ", "_")

        folder_path = os.path.join(SPECIAL_BACKUP_FOLDER, safe_name)

        # remplace l'ancien backup si il existe
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

        os.makedirs(folder_path)

        backup_path = os.path.join(folder_path, TARGET_FILE)

        shutil.copy2(TARGET_PATH, backup_path)

        print(f"⭐ Named backup created: {safe_name}")

        self.refresh_list()

    def reload_backup(self):

        selection = self.listbox.curselection()

        if not selection:
            messagebox.showinfo("Reload", "Select a backup first")
            return

        entry = self.listbox.get(selection[0])
        name = entry.split("   ", 1)[1]

        folder = os.path.join(SPECIAL_BACKUP_FOLDER, name)

        backup_file = os.path.join(folder, TARGET_FILE)

        if not os.path.exists(backup_file):
            messagebox.showerror("Error", "Backup file missing")
            return

        confirm = messagebox.askyesno(
            "Confirm",
            f"Reload backup '{name}' ?"
        )

        if not confirm:
            return

        create_restore_safety_backup()

        shutil.copy2(backup_file, TARGET_PATH)

        print(f"🔄 Reloaded backup: {name}")

    def clean_backups(self):

        folders = [
            f for f in os.listdir(SPECIAL_BACKUP_FOLDER)
            if os.path.isdir(os.path.join(SPECIAL_BACKUP_FOLDER, f))
        ]

        folders.sort(
            key=lambda f: os.path.getctime(os.path.join(SPECIAL_BACKUP_FOLDER, f)),
            reverse=True
        )

        to_delete = folders[5:]

        safety_files = [
            f for f in os.listdir(SAFETY_FOLDER)
            if os.path.isfile(os.path.join(SAFETY_FOLDER, f))
        ]

        safety_files.sort(
            key=lambda f: os.path.getctime(os.path.join(SAFETY_FOLDER, f)),
            reverse=True
        )

        safety_to_delete = safety_files[5:]

        if not to_delete and not safety_to_delete:
            messagebox.showinfo("Clean Backups", "Nothing to delete (5 or fewer backups)")
            return

        confirm = messagebox.askyesno(
            "Clean Backups",
            f"Delete {len(to_delete)} backup(s) and {len(safety_to_delete)} safety backup(s), keeping the 5 most recent of each ?"
        )

        if not confirm:
            return

        for f in to_delete:
            shutil.rmtree(os.path.join(SPECIAL_BACKUP_FOLDER, f))
            print(f"🗑 Deleted backup: {f}")

        for f in safety_to_delete:
            os.remove(os.path.join(SAFETY_FOLDER, f))
            print(f"🗑 Deleted safety backup: {f}")

        self.refresh_list()


if __name__ == "__main__":

    root = tk.Tk()

    ui = SaveManagerUI(root)

    root.mainloop()