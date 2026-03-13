import os
import sys
import json
import shutil
import random
import threading
import tkinter as tk
from tkinter import ttk

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

def _play_sound(path, volume: float = 1.0):
    """Play a sound file in a background thread (non-blocking)."""
    def _run():
        try:
            sound = pygame.mixer.Sound(path)
            sound.set_volume(max(0.0, min(1.0, volume)))
            sound.play()
        except Exception as e:
            print(f"[sound] Error playing {path}: {e}")
    threading.Thread(target=_run, daemon=True).start()


def _center_window(win, width, height):
    """Position *win* at the center of the screen."""
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x  = (sw - width)  // 2
    y  = (sh - height) // 2
    win.geometry(f"{width}x{height}+{x}+{y}")


def _set_icon(win):
    """Apply assets/poop_icon.ico to *win* (silently ignored if missing)."""
    try:
        ico = os.path.join(_base_path(), "assets", "poop_icon.ico")
        win.iconbitmap(ico)
    except Exception as e:
        print(f"[icon] Could not set icon: {e}")


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

SOUND_CONFIG_PATH  = os.path.join(CUSTOM_FOLDER, "sound_config.json")
WINDOW_CONFIG_PATH = os.path.join(CUSTOM_FOLDER, "window_config.json")


def _load_sound_config() -> dict:
    """Load sound config from disk, falling back to defaults for missing keys."""
    default = {
        "mode":        "random",
        "save_backup": None,
        "quick_save":  None,
        "quick_load":  None,
        "volume":      1.0,
        "mute":        False,
    }
    try:
        if os.path.exists(SOUND_CONFIG_PATH):
            with open(SOUND_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            default.update(data)
    except Exception as e:
        print(f"[config] Failed to load sound config: {e}")
    return default


def _save_sound_config(config: dict) -> None:
    """Persist sound config to disk."""
    try:
        with open(SOUND_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"[config] Failed to save sound config: {e}")


def _load_window_config(key: str = "main") -> dict | None:
    """Return saved position {x, y} for *key*, or None if unavailable."""
    try:
        if os.path.exists(WINDOW_CONFIG_PATH):
            with open(WINDOW_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Migrate old flat format {"x":…, "y":…}
            if "x" in data and "main" not in data:
                return {"x": data["x"], "y": data["y"]} if key == "main" else None
            return data.get(key)
    except Exception as e:
        print(f"[config] Failed to load window config: {e}")
    return None


def _save_window_config(key: str, x: int, y: int) -> None:
    """Persist position for *key* to disk (other keys are preserved)."""
    try:
        data = {}
        if os.path.exists(WINDOW_CONFIG_PATH):
            with open(WINDOW_CONFIG_PATH, "r", encoding="utf-8") as f:
                existing = json.load(f)
            # Migrate old flat format on first write
            if "x" in existing and "main" not in existing:
                data["main"] = {"x": existing["x"], "y": existing["y"]}
            else:
                data = existing
        data[key] = {"x": x, "y": y}
        with open(WINDOW_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"[config] Failed to save window config: {e}")


def create_restore_safety_backup():

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safety_name = f"safety_{timestamp}.sav"
    safety_path = os.path.join(SAFETY_FOLDER, safety_name)

    shutil.copy2(TARGET_PATH, safety_path)

    print(f"🛟 Safety backup created: {safety_name}")


def _collect_all_mp3s():
    """Return a sorted list of absolute paths for every mp3 under fx/."""
    fx_root = os.path.join(_base_path(), "fx")
    mp3s = []
    for dirpath, _, files in os.walk(fx_root):
        for f in sorted(files):
            if f.lower().endswith(".mp3"):
                mp3s.append(os.path.join(dirpath, f))
    mp3s.sort()
    return mp3s


# Sentinel values for "random pool" options in Custom mode
RANDOM_FART = "__random_fart__"
RANDOM_BURP = "__random_burp__"

# sentinel → display label  (order = order shown in dropdown)
_SPECIAL_SOUND_LABELS = {
    RANDOM_FART: "🎲  All Fart (random)",
    RANDOM_BURP: "🎲  All Burp (random)",
}
# display label → sentinel  (reverse map)
_SPECIAL_SOUND_VALUES = {v: k for k, v in _SPECIAL_SOUND_LABELS.items()}


class SoundManagerWindow:
    """Toplevel window to configure sound behaviour per action."""

    ACTIONS = [
        ("save_backup", "Save Backup"),
        ("quick_save",  "Quick Save (F7)"),
        ("quick_load",  "Quick Load (F9)"),
    ]

    def __init__(self, parent, sound_config, topmost: bool = False):
        self.window = tk.Toplevel(parent)
        self.window.title("Sound Manager")
        self.window.resizable(False, False)
        self.window.attributes("-topmost", topmost)
        self.window.grab_set()
        self.sound_config = sound_config
        _set_icon(self.window)

        sm_cfg = _load_window_config("sound_manager")
        if sm_cfg:
            self.window.geometry(f"500x390+{sm_cfg['x']}+{sm_cfg['y']}")
        else:
            _center_window(self.window, 500, 390)

        self._save_pos_job = None
        self.window.bind("<Configure>", self._on_window_configure)

        # Build mp3 list
        self.all_mp3s  = _collect_all_mp3s()
        base           = _base_path()
        self.mp3_labels = (
            ["(none)"]
            + list(_SPECIAL_SOUND_LABELS.values())          # special random-pool entries
            + [os.path.relpath(p, base) for p in self.all_mp3s]
        )
        # Number of non-file entries before the actual mp3 paths
        self._mp3_offset = 1 + len(_SPECIAL_SOUND_LABELS)  # "(none)" + specials

        # --- Mode selection ---
        mode_frame = tk.LabelFrame(self.window, text="Sound Mode", padx=8, pady=5)
        mode_frame.pack(fill="x", padx=12, pady=(10, 5))

        self.mode_var = tk.StringVar(value=sound_config.get("mode", "random"))

        for value, text in [
            ("random",  "🎲  Random  (fart on save actions · burp on load)"),
            ("classic", "🎵  Classic  (fx/save.mp3  ·  fx/load.mp3)"),
            ("custom",  "🎛   Custom assignment (choose a file per action)"),
        ]:
            tk.Radiobutton(
                mode_frame, text=text,
                variable=self.mode_var, value=value,
                command=self._on_mode_change,
                anchor="w"
            ).pack(fill="x")

        # --- Custom assignment ---
        self.custom_frame = tk.LabelFrame(
            self.window, text="Custom Sound Assignment", padx=8, pady=5
        )
        self.custom_frame.pack(fill="both", expand=True, padx=12, pady=5)

        self.combos       = {}
        self.preview_btns = {}

        for action, label in self.ACTIONS:
            row = tk.Frame(self.custom_frame)
            row.pack(fill="x", pady=4)

            tk.Label(row, text=label, width=18, anchor="w").pack(side="left")

            current_path = sound_config.get(action)
            try:
                if current_path in _SPECIAL_SOUND_LABELS:
                    # it's a sentinel → find its display label in mp3_labels
                    idx = self.mp3_labels.index(_SPECIAL_SOUND_LABELS[current_path])
                elif current_path in self.all_mp3s:
                    idx = self.all_mp3s.index(current_path) + self._mp3_offset
                else:
                    idx = 0
            except (ValueError, TypeError):
                idx = 0

            combo = ttk.Combobox(row, values=self.mp3_labels, state="readonly", width=34)
            combo.current(idx)
            combo.pack(side="left", padx=4)
            self.combos[action] = combo

            btn = tk.Button(row, text="▶", width=3,
                            command=lambda a=action: self._preview(a))
            btn.pack(side="left")
            self.preview_btns[action] = btn

        # --- Volume & Mute ---
        vol_frame = tk.LabelFrame(self.window, text="Global Volume", padx=8, pady=4)
        vol_frame.pack(fill="x", padx=12, pady=(0, 5))

        self.volume_var = tk.IntVar(value=int(sound_config.get("volume", 1.0) * 100))
        self.mute_var   = tk.BooleanVar(value=sound_config.get("mute", False))

        vol_row = tk.Frame(vol_frame)
        vol_row.pack(fill="x")

        self.vol_scale = tk.Scale(
            vol_row, from_=0, to=100, orient="horizontal",
            variable=self.volume_var, showvalue=False,
            command=self._on_volume_change
        )
        self.vol_scale.pack(side="left", fill="x", expand=True)

        self.vol_label = tk.Label(vol_row, text=f"{self.volume_var.get()} %", width=6)
        self.vol_label.pack(side="left")

        tk.Checkbutton(vol_row, text="Mute", variable=self.mute_var).pack(side="left", padx=(8, 0))

        # --- Save / Cancel ---
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text="Save",   width=10, command=self._save).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancel", width=10, command=self.window.destroy).pack(side="left", padx=5)

        self._on_mode_change()

    # ------------------------------------------------------------------

    def _on_volume_change(self, _=None):
        self.vol_label.config(text=f"{self.volume_var.get()} %")

    def _on_window_configure(self, event):
        if event.widget is not self.window:
            return
        if self._save_pos_job:
            self.window.after_cancel(self._save_pos_job)
        self._save_pos_job = self.window.after(500, self._persist_window_position)

    def _persist_window_position(self):
        _save_window_config("sound_manager", self.window.winfo_x(), self.window.winfo_y())
        self._save_pos_job = None

    def _on_mode_change(self):
        is_custom = self.mode_var.get() == "custom"
        combo_state = "readonly" if is_custom else "disabled"
        btn_state   = "normal"   if is_custom else "disabled"
        for action in self.combos:
            self.combos[action].config(state=combo_state)
            self.preview_btns[action].config(state=btn_state)

    def _preview(self, action):
        label = self.combos[action].get()
        if label == "(none)":
            return
        # special random-pool entries
        if label in _SPECIAL_SOUND_VALUES:
            sentinel = _SPECIAL_SOUND_VALUES[label]
            try:
                if sentinel == RANDOM_FART:
                    files = [os.path.join(FX_FART_FOLDER, f) for f in os.listdir(FX_FART_FOLDER) if f.lower().endswith(".mp3")]
                else:
                    files = [os.path.join(FX_BURP_FOLDER, f) for f in os.listdir(FX_BURP_FOLDER) if f.lower().endswith(".mp3")]
                if files:
                    _play_sound(random.choice(files), volume=self.volume_var.get() / 100)
            except Exception as e:
                messagebox.showerror("Preview Error", str(e), parent=self.window)
            return
        # regular mp3 file
        try:
            idx = self.mp3_labels.index(label) - self._mp3_offset
            _play_sound(self.all_mp3s[idx], volume=self.volume_var.get() / 100)
        except Exception as e:
            messagebox.showerror("Preview Error", str(e), parent=self.window)

    def _save(self):
        self.sound_config["mode"]   = self.mode_var.get()
        self.sound_config["volume"] = self.volume_var.get() / 100
        self.sound_config["mute"]   = self.mute_var.get()
        for action in self.combos:
            label = self.combos[action].get()
            if label == "(none)":
                self.sound_config[action] = None
            elif label in _SPECIAL_SOUND_VALUES:
                self.sound_config[action] = _SPECIAL_SOUND_VALUES[label]
            else:
                try:
                    idx = self.mp3_labels.index(label) - self._mp3_offset
                    self.sound_config[action] = self.all_mp3s[idx]
                except (ValueError, IndexError):
                    self.sound_config[action] = None
        self.window.destroy()


class SaveManagerUI:

    def __init__(self, root):

        self.root = root
        root.withdraw()   # hide until fully built to avoid visual flash

        # Sound configuration – loaded from disk, persisted on every Save in Sound Manager
        self.sound_config = _load_sound_config()

        root.title("Mewgenics Save Manager")
        root.attributes("-topmost", True)
        _set_icon(root)

        win_cfg = _load_window_config("main")
        if win_cfg:
            root.geometry(f"480x420+{win_cfg['x']}+{win_cfg['y']}")
        else:
            _center_window(root, 480, 420)

        self._save_pos_job = None
        root.bind("<Configure>", self._on_window_configure)

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

        self.sound_manager_button = tk.Button(
            action_frame,
            text="🔊 Sound Manager",
            command=self.open_sound_manager
        )
        self.sound_manager_button.pack(side="left", padx=5)

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


        self.version_label = tk.Label(bottom_frame, text=f"v{APP_VERSION}", fg="gray", font=("Arial", 8))
        self.version_label.pack(side="right")

        self.refresh_list()
        root.deiconify()  # show now that everything is ready

    # ------------------------------------------------------------------

    def open_sound_manager(self):
        win = SoundManagerWindow(self.root, self.sound_config, topmost=self.topmost_var.get())
        self.root.wait_window(win.window)   # block until window is closed
        _save_sound_config(self.sound_config)

    def _play_sound_for_action(self, action):
        """Play the sound associated with *action*, respecting mode & mute."""
        if self.sound_config.get("mute", False):
            return

        mode   = self.sound_config.get("mode", "random")
        volume = self.sound_config.get("volume", 1.0)
        base   = _base_path()

        if mode == "random":
            if action in ("save_backup", "quick_save"):
                farts = [
                    os.path.join(FX_FART_FOLDER, f)
                    for f in os.listdir(FX_FART_FOLDER)
                    if f.lower().endswith(".mp3")
                ]
                if farts:
                    _play_sound(random.choice(farts), volume=volume)
            elif action == "quick_load":
                burps = [
                    os.path.join(FX_BURP_FOLDER, f)
                    for f in os.listdir(FX_BURP_FOLDER)
                    if f.lower().endswith(".mp3")
                ]
                if burps:
                    _play_sound(random.choice(burps), volume=volume)

        elif mode == "classic":
            if action in ("save_backup", "quick_save"):
                _play_sound(os.path.join(base, "fx", "save.mp3"), volume=volume)
            elif action == "quick_load":
                _play_sound(os.path.join(base, "fx", "load.mp3"), volume=volume)

        elif mode == "custom":
            path = self.sound_config.get(action)
            if path == RANDOM_FART:
                farts = [
                    os.path.join(FX_FART_FOLDER, f)
                    for f in os.listdir(FX_FART_FOLDER)
                    if f.lower().endswith(".mp3")
                ]
                if farts:
                    _play_sound(random.choice(farts), volume=volume)
            elif path == RANDOM_BURP:
                burps = [
                    os.path.join(FX_BURP_FOLDER, f)
                    for f in os.listdir(FX_BURP_FOLDER)
                    if f.lower().endswith(".mp3")
                ]
                if burps:
                    _play_sound(random.choice(burps), volume=volume)
            elif path and os.path.exists(path):
                _play_sound(path, volume=volume)

    def toggle_topmost(self):
        self.root.attributes("-topmost", self.topmost_var.get())

    def _on_window_configure(self, event):
        """Debounce: save position 500 ms after the last move."""
        if event.widget is not self.root:
            return
        if self._save_pos_job:
            self.root.after_cancel(self._save_pos_job)
        self._save_pos_job = self.root.after(500, self._persist_window_position)

    def _persist_window_position(self):
        _save_window_config("main", self.root.winfo_x(), self.root.winfo_y())
        self._save_pos_job = None

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
            self.listbox.insert(tk.END, f"{date_str}   {f}")

    def quick_load(self, confirm=True):

        if self.listbox.size() == 0:
            messagebox.showinfo("Quick Load", "No backup available")
            return

        entry = self.listbox.get(0)
        name  = entry.split("   ", 1)[1]

        folder      = os.path.join(SPECIAL_BACKUP_FOLDER, name)
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
            self._play_sound_for_action("quick_load")
            print(f"⚡ Quick loaded: {name}")
        except Exception as e:
            messagebox.showerror("Quick Load Error", str(e))
            print(f"❌ Quick load failed: {e}")

    def create_quick_save(self):

        name        = f"quicksave_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        folder_path = os.path.join(SPECIAL_BACKUP_FOLDER, name)

        try:
            os.makedirs(folder_path)
            shutil.copy2(TARGET_PATH, os.path.join(folder_path, TARGET_FILE))
            self._play_sound_for_action("quick_save")
            print(f"⚡ Quick save created: {name}")
        except Exception as e:
            messagebox.showerror("Quick Save Error", str(e))
            print(f"❌ Quick save failed: {e}")

        self.refresh_list()

    def create_named_backup(self):

        name = simpledialog.askstring("Backup Name", "Enter backup name:")

        if not name:
            return

        safe_name   = name.replace(" ", "_")
        folder_path = os.path.join(SPECIAL_BACKUP_FOLDER, safe_name)

        # remplace l'ancien backup si il existe
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

        os.makedirs(folder_path)

        backup_path = os.path.join(folder_path, TARGET_FILE)
        shutil.copy2(TARGET_PATH, backup_path)
        self._play_sound_for_action("save_backup")
        print(f"⭐ Named backup created: {safe_name}")

        self.refresh_list()

    def reload_backup(self):

        selection = self.listbox.curselection()

        if not selection:
            messagebox.showinfo("Reload", "Select a backup first")
            return

        entry = self.listbox.get(selection[0])
        name  = entry.split("   ", 1)[1]

        folder      = os.path.join(SPECIAL_BACKUP_FOLDER, name)
        backup_file = os.path.join(folder, TARGET_FILE)

        if not os.path.exists(backup_file):
            messagebox.showerror("Error", "Backup file missing")
            return

        confirm = messagebox.askyesno("Confirm", f"Reload backup '{name}' ?")
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
    ui   = SaveManagerUI(root)
    root.mainloop()

