import os
import shutil
import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime


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

BACKUP_FOLDER = os.path.join(CUSTOM_FOLDER, "backups")
SPECIAL_BACKUP_FOLDER = os.path.join(CUSTOM_FOLDER, "named_backups")
SAFETY_FOLDER = os.path.join(CUSTOM_FOLDER, "restore_safety")

os.makedirs(BACKUP_FOLDER, exist_ok=True)
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

    def delete_backup(self):

        selection = self.listbox.curselection()

        if not selection:
            return

        entry = self.listbox.get(selection[0])
        name = entry.split("   ", 1)[1]

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

    root = tk.Tk()

    ui = SaveManagerUI(root)

    root.mainloop()