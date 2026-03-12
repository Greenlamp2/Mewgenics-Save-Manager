import os
import shutil
import threading
import time
import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime
import subprocess

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


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
print(WATCH_FOLDER)

TARGET_FILE = "steamcampaign01.sav"
TARGET_PATH = os.path.join(WATCH_FOLDER, TARGET_FILE)

CUSTOM_FOLDER = os.path.join(WATCH_FOLDER, "custom")

BACKUP_FOLDER = os.path.join(CUSTOM_FOLDER, "backups")
SPECIAL_BACKUP_FOLDER = os.path.join(CUSTOM_FOLDER, "named_backups")
SAFETY_FOLDER = os.path.join(CUSTOM_FOLDER, "restore_safety")

MAX_BACKUPS = 20
COOLDOWN = 1
last_backup_time = 0

os.makedirs(BACKUP_FOLDER, exist_ok=True)
os.makedirs(SPECIAL_BACKUP_FOLDER, exist_ok=True)
os.makedirs(SAFETY_FOLDER, exist_ok=True)

def create_backup():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{TARGET_FILE}_{timestamp}.sav"
    backup_path = os.path.join(BACKUP_FOLDER, backup_name)

    shutil.copy2(TARGET_PATH, backup_path)

    cleanup_backups()

    print(f"✅ Backup created: {backup_name}")


def cleanup_backups():

    backups = [
        os.path.join(BACKUP_FOLDER, f)
        for f in os.listdir(BACKUP_FOLDER)
        if f.endswith(".sav")
    ]

    backups.sort(key=os.path.getmtime)

    while len(backups) > MAX_BACKUPS:
        oldest = backups.pop(0)
        os.remove(oldest)


def create_restore_safety_backup():

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safety_name = f"safety_{timestamp}.sav"
    safety_path = os.path.join(SAFETY_FOLDER, safety_name)

    shutil.copy2(TARGET_PATH, safety_path)

    print(f"🛟 Safety backup created: {safety_name}")


class ChangeHandler(FileSystemEventHandler):

    def on_modified(self, event):

        global last_backup_time

        if not event.is_directory and event.src_path.endswith(TARGET_FILE):

            if time.time() - last_backup_time < COOLDOWN:
                return

            last_backup_time = time.time()

            create_backup()


def start_watcher():

    event_handler = ChangeHandler()

    observer = Observer()

    observer.schedule(event_handler, WATCH_FOLDER, recursive=False)

    observer.start()

    print("👀 Watching save file...")

    while True:
        time.sleep(1)


class SaveManagerUI:

    def __init__(self, root):

        self.root = root

        root.title("Mewgenics Save Manager")
        root.geometry("320x400")
        root.attributes("-topmost", True)

        self.save_button = tk.Button(
            root,
            text="Save Backup",
            height=2,
            command=self.create_named_backup
        )

        self.save_button.pack(pady=10)

        self.listbox = tk.Listbox(root)

        self.listbox.pack(fill="both", expand=True, padx=10)

        self.reload_button = tk.Button(
            root,
            text="Reload Selected",
            command=self.reload_backup
        )

        self.reload_button.pack(pady=5)

        self.delete_button = tk.Button(
            root,
            text="Delete Selected",
            command=self.delete_backup
        )

        self.delete_button.pack(pady=5)

        # self.check_button = tk.Button(
        #     root,
        #     text="Check Folder Structure",
        #     command=self.check_folders
        # )
        #
        # self.check_button.pack(pady=5)
        #
        # self.debug_button = tk.Button(
        #     root,
        #     text="Debug Info",
        #     command=self.debug_info
        # )
        #
        # self.debug_button.pack(pady=5)
        #
        # self.permission_button = tk.Button(
        #     root,
        #     text="Test Permissions",
        #     command=self.test_permissions
        # )
        #
        # self.permission_button.pack(pady=5)
        #
        # self.open_button = tk.Button(
        #     root,
        #     text="Open Save Folder",
        #     command=self.open_save_folder
        # )
        #
        # self.open_button.pack(pady=5)

        self.refresh_list()


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

    def debug_info(self):

        info = []

        info.append(f"USER_HOME: {USER_HOME}")
        info.append(f"WATCH_FOLDER: {WATCH_FOLDER}")
        info.append(f"TARGET_PATH: {TARGET_PATH}")
        info.append("")

        info.append(f"WATCH_FOLDER exists: {os.path.exists(WATCH_FOLDER)}")
        info.append(f"TARGET_FILE exists: {os.path.exists(TARGET_PATH)}")
        info.append(f"CUSTOM_FOLDER exists: {os.path.exists(CUSTOM_FOLDER)}")
        info.append(f"BACKUP_FOLDER exists: {os.path.exists(BACKUP_FOLDER)}")
        info.append(f"SPECIAL_BACKUP_FOLDER exists: {os.path.exists(SPECIAL_BACKUP_FOLDER)}")
        info.append(f"SAFETY_FOLDER exists: {os.path.exists(SAFETY_FOLDER)}")

        messagebox.showinfo(
            "Debug Info",
            "\n".join(info)
        )

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

    def open_save_folder(self):

        if os.path.exists(WATCH_FOLDER):
            subprocess.Popen(f'explorer "{WATCH_FOLDER}"')
        else:
            messagebox.showerror("Error", "Save folder does not exist")

    def test_permissions(self):

        report = []

        try:

            os.makedirs(WATCH_FOLDER, exist_ok=True)
            report.append("✅ WATCH_FOLDER accessible")

        except Exception as e:
            report.append(f"❌ Cannot access WATCH_FOLDER : {e}")
            messagebox.showerror("Permissions", "\n".join(report))
            return

        test_folder = os.path.join(WATCH_FOLDER, "permission_test")

        try:

            os.makedirs(test_folder, exist_ok=True)
            report.append("✅ Folder creation allowed")

        except Exception as e:
            report.append(f"❌ Cannot create folder : {e}")

        test_file = os.path.join(test_folder, "test.txt")

        try:

            with open(test_file, "w") as f:
                f.write("permission test")

            report.append("✅ File creation allowed")

        except Exception as e:
            report.append(f"❌ Cannot create file : {e}")

        copied_file = os.path.join(test_folder, "copy_test.txt")

        try:

            shutil.copy2(test_file, copied_file)
            report.append("✅ File copy allowed")

        except Exception as e:
            report.append(f"❌ Cannot copy file : {e}")

        try:

            os.remove(test_file)
            os.remove(copied_file)
            os.rmdir(test_folder)

            report.append("🧹 Test files cleaned")

        except Exception as e:
            report.append(f"⚠ Cleanup issue : {e}")

        messagebox.showinfo(
            "Permission Test",
            "\n".join(report)
        )

    def check_folders(self):

        folders = [
            ("WATCH_FOLDER", WATCH_FOLDER),
            ("CUSTOM_FOLDER", CUSTOM_FOLDER),
            ("BACKUP_FOLDER", BACKUP_FOLDER),
            ("SPECIAL_BACKUP_FOLDER", SPECIAL_BACKUP_FOLDER),
            ("SAFETY_FOLDER", SAFETY_FOLDER),
        ]

        report = []

        for name, path in folders:

            if os.path.exists(path):
                report.append(f"✅ {name} exists")
            else:
                try:
                    os.makedirs(path, exist_ok=True)
                    report.append(f"🛠 Created {name}")
                except Exception as e:
                    report.append(f"❌ Failed {name} : {e}")

        messagebox.showinfo(
            "Folder Check",
            "\n".join(report)
        )

    def delete_backup(self):

        selection = self.listbox.curselection()

        if not selection:
            return

        name = self.listbox.get(selection[0])

        confirm = messagebox.askyesno(
            "Delete",
            f"Delete backup '{name}' ?"
        )

        if not confirm:
            return

        folder = os.path.join(SPECIAL_BACKUP_FOLDER, name)

        shutil.rmtree(folder)

        print(f"🗑 Deleted backup: {name}")

        self.refresh_list()


if __name__ == "__main__":

    # threading.Thread(target=start_watcher, daemon=True).start()

    root = tk.Tk()

    ui = SaveManagerUI(root)

    root.mainloop()