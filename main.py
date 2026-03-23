import os
import sys
import json
import shutil
import random
import threading
from datetime import datetime

import keyboard
import pygame

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QCheckBox, QSlider,
    QGroupBox, QRadioButton, QButtonGroup, QComboBox,
    QMessageBox, QInputDialog, QSizePolicy, QFileDialog,
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QIcon, QPixmap, QPainter

APP_VERSION = "1.0.11"

# ---------------------------------------------------------------------------
# Palette-relative widget styles (adaptés dark & light)
# ---------------------------------------------------------------------------

_CHECKBOX_STYLE = """
    QCheckBox { spacing: 6px; }
    QCheckBox::indicator {
        width: 16px; height: 16px;
        border: 2px solid palette(mid);
        border-radius: 3px;
        background: palette(base);
    }
    QCheckBox::indicator:hover { border-color: palette(highlight); }
    QCheckBox::indicator:checked {
        background: palette(highlight);
        border-color: palette(highlight);
    }
"""

_RADIOBUTTON_STYLE = """
    QRadioButton { spacing: 6px; }
    QRadioButton::indicator {
        width: 14px; height: 14px;
        border: 2px solid palette(mid);
        border-radius: 8px;
        background: palette(base);
    }
    QRadioButton::indicator:hover { border-color: palette(highlight); }
    QRadioButton::indicator:checked {
        background: palette(highlight);
        border-color: palette(highlight);
    }
"""

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def _base_path():
    """Return the folder that contains bundled resources (sys._MEIPASS when frozen)."""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def _user_path():
    """Return the folder that contains the running EXE (or script when not frozen).
    Users can place additional MP3s in an 'fx/' sub-folder here."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _get_fart_files() -> list[str]:
    seen, files = set(), []
    for base in dict.fromkeys([_base_path(), _user_path()]):
        folder = os.path.join(base, "fx", "fart")
        if os.path.isdir(folder):
            for f in os.listdir(folder):
                if f.lower().endswith(".mp3"):
                    full = os.path.normpath(os.path.join(folder, f))
                    if full not in seen:
                        seen.add(full)
                        files.append(full)
    return files


def _get_burp_files() -> list[str]:
    seen, files = set(), []
    for base in dict.fromkeys([_base_path(), _user_path()]):
        folder = os.path.join(base, "fx", "burp")
        if os.path.isdir(folder):
            for f in os.listdir(folder):
                if f.lower().endswith(".mp3"):
                    full = os.path.normpath(os.path.join(folder, f))
                    if full not in seen:
                        seen.add(full)
                        files.append(full)
    return files


# ---------------------------------------------------------------------------
# Pygame sound
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Window helpers
# ---------------------------------------------------------------------------

def _apply_dark_palette(app: QApplication) -> None:
    from PySide6.QtGui import QPalette, QColor
    p = QPalette()
    dark   = QColor(53, 53, 53)
    darker = QColor(35, 35, 35)
    white  = Qt.GlobalColor.white
    blue   = QColor(42, 130, 218)
    p.setColor(QPalette.ColorRole.Window,          dark)
    p.setColor(QPalette.ColorRole.WindowText,      white)
    p.setColor(QPalette.ColorRole.Base,            darker)
    p.setColor(QPalette.ColorRole.AlternateBase,   dark)
    p.setColor(QPalette.ColorRole.ToolTipBase,     QColor(25, 25, 25))
    p.setColor(QPalette.ColorRole.ToolTipText,     white)
    p.setColor(QPalette.ColorRole.Text,            white)
    p.setColor(QPalette.ColorRole.Button,          dark)
    p.setColor(QPalette.ColorRole.ButtonText,      white)
    p.setColor(QPalette.ColorRole.BrightText,      Qt.GlobalColor.red)
    p.setColor(QPalette.ColorRole.Link,            blue)
    p.setColor(QPalette.ColorRole.Highlight,       blue)
    p.setColor(QPalette.ColorRole.HighlightedText, darker)
    app.setPalette(p)


def _apply_light_palette(app: QApplication) -> None:
    from PySide6.QtGui import QPalette, QColor
    p = QPalette()
    gray    = QColor(240, 240, 240)   # classic Windows control face
    white   = QColor(255, 255, 255)
    dark    = QColor(0,   0,   0)
    mid     = QColor(160, 160, 160)
    shadow  = QColor(105, 105, 105)
    blue    = QColor(0,   120, 215)   # Windows 10 accent
    p.setColor(QPalette.ColorRole.Window,          gray)
    p.setColor(QPalette.ColorRole.WindowText,      dark)
    p.setColor(QPalette.ColorRole.Base,            white)
    p.setColor(QPalette.ColorRole.AlternateBase,   QColor(233, 231, 227))
    p.setColor(QPalette.ColorRole.ToolTipBase,     white)
    p.setColor(QPalette.ColorRole.ToolTipText,     dark)
    p.setColor(QPalette.ColorRole.Text,            dark)
    p.setColor(QPalette.ColorRole.Button,          gray)
    p.setColor(QPalette.ColorRole.ButtonText,      dark)
    p.setColor(QPalette.ColorRole.BrightText,      QColor(255, 0, 0))
    p.setColor(QPalette.ColorRole.Link,            blue)
    p.setColor(QPalette.ColorRole.Highlight,       blue)
    p.setColor(QPalette.ColorRole.HighlightedText, white)
    p.setColor(QPalette.ColorRole.Mid,             mid)
    p.setColor(QPalette.ColorRole.Shadow,          shadow)
    app.setPalette(p)


def _center_window(win: QWidget, width: int, height: int):
    screen = QApplication.primaryScreen().availableGeometry()
    x = screen.x() + (screen.width() - width) // 2
    y = screen.y() + (screen.height() - height) // 2
    win.setGeometry(x, y, width, height)


def _make_icon_from_svg(svg_path: str) -> QIcon:
    """Render the SVG at several sizes onto a fully transparent QPixmap."""
    from PySide6.QtSvg import QSvgRenderer
    renderer = QSvgRenderer(svg_path)
    icon = QIcon()
    for size in (16, 32, 48, 64, 128, 256):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        icon.addPixmap(pixmap)
    return icon


def _set_icon(win: QWidget):
    try:
        svg = os.path.join(_base_path(), "assets", "poop_icon.svg")
        if os.path.exists(svg):
            win.setWindowIcon(_make_icon_from_svg(svg))
        else:
            ico = os.path.join(_base_path(), "assets", "poop_icon.ico")
            win.setWindowIcon(QIcon(ico))
    except Exception as e:
        print(f"[icon] Could not set icon: {e}")


# ---------------------------------------------------------------------------
# Steam save folder detection
# ---------------------------------------------------------------------------

def detect_steam_save_folder():
    appdata = os.getenv("APPDATA")
    mewgenics_root = os.path.join(appdata, "Glaiel Games", "Mewgenics")
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
TARGET_FILE  = "steamcampaign01.sav"
TARGET_PATH  = os.path.join(WATCH_FOLDER, TARGET_FILE)

CUSTOM_FOLDER         = os.path.join(WATCH_FOLDER, "custom")
SPECIAL_BACKUP_FOLDER = os.path.join(CUSTOM_FOLDER, "named_backups")
SAFETY_FOLDER         = os.path.join(CUSTOM_FOLDER, "restore_safety")

os.makedirs(SPECIAL_BACKUP_FOLDER, exist_ok=True)
os.makedirs(SAFETY_FOLDER, exist_ok=True)

SOUND_CONFIG_PATH  = os.path.join(CUSTOM_FOLDER, "sound_config.json")
WINDOW_CONFIG_PATH = os.path.join(CUSTOM_FOLDER, "window_config.json")


# ---------------------------------------------------------------------------
# Config persistence
# ---------------------------------------------------------------------------

def _load_sound_config() -> dict:
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
    try:
        with open(SOUND_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"[config] Failed to save sound config: {e}")


def _load_window_config(key: str = "main") -> dict | None:
    try:
        if os.path.exists(WINDOW_CONFIG_PATH):
            with open(WINDOW_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "x" in data and "main" not in data:
                return {"x": data["x"], "y": data["y"]} if key == "main" else None
            return data.get(key)
    except Exception as e:
        print(f"[config] Failed to load window config: {e}")
    return None


def _save_window_config(key: str, x: int, y: int) -> None:
    try:
        data = {}
        if os.path.exists(WINDOW_CONFIG_PATH):
            with open(WINDOW_CONFIG_PATH, "r", encoding="utf-8") as f:
                existing = json.load(f)
            if "x" in existing and "main" not in existing:
                data["main"] = {"x": existing["x"], "y": existing["y"]}
            else:
                data = existing
        data[key] = {"x": x, "y": y}
        with open(WINDOW_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"[config] Failed to save window config: {e}")


def _load_theme() -> str:
    """Return 'dark' (default) or 'light'."""
    try:
        if os.path.exists(WINDOW_CONFIG_PATH):
            with open(WINDOW_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("theme", "dark")
    except Exception:
        pass
    return "dark"


def _save_theme(theme: str) -> None:
    try:
        data: dict = {}
        if os.path.exists(WINDOW_CONFIG_PATH):
            with open(WINDOW_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        data["theme"] = theme
        with open(WINDOW_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"[config] Failed to save theme: {e}")


# ---------------------------------------------------------------------------
# Safety backup
# ---------------------------------------------------------------------------

def create_restore_safety_backup():
    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    safety_name = f"safety_{timestamp}.sav"
    safety_path = os.path.join(SAFETY_FOLDER, safety_name)
    shutil.copy2(TARGET_PATH, safety_path)
    print(f"🛟 Safety backup created: {safety_name}")


# ---------------------------------------------------------------------------
# MP3 collection helpers
# ---------------------------------------------------------------------------

def _collect_all_mp3s() -> list[str]:
    seen, mp3s = set(), []
    for base in dict.fromkeys([_base_path(), _user_path()]):
        fx_root = os.path.join(base, "fx")
        if not os.path.isdir(fx_root):
            continue
        for dirpath, _, files in os.walk(fx_root):
            for f in sorted(files):
                if f.lower().endswith(".mp3"):
                    full = os.path.normpath(os.path.join(dirpath, f))
                    if full not in seen:
                        seen.add(full)
                        mp3s.append(full)
    mp3s.sort()
    return mp3s


def _mp3_display_label(path: str) -> str:
    base_p = _base_path()
    user_p = _user_path()
    try:
        rel = os.path.relpath(path, base_p)
        if not rel.startswith(".."):
            return rel.replace("\\", "/")
    except ValueError:
        pass
    try:
        rel = os.path.relpath(path, user_p)
        return f"[user] {rel.replace(chr(92), '/')}"
    except ValueError:
        return os.path.basename(path)


# ---------------------------------------------------------------------------
# Sound sentinel values
# ---------------------------------------------------------------------------

RANDOM_FART = "__random_fart__"
RANDOM_BURP = "__random_burp__"

_SPECIAL_SOUND_LABELS = {
    RANDOM_FART: "🎲  All Fart (random)",
    RANDOM_BURP: "🎲  All Burp (random)",
}
_SPECIAL_SOUND_VALUES = {v: k for k, v in _SPECIAL_SOUND_LABELS.items()}


# ---------------------------------------------------------------------------
# Sound Manager Dialog
# ---------------------------------------------------------------------------

class SoundManagerDialog(QDialog):

    ACTIONS = [
        ("save_backup", "Save Backup"),
        ("quick_save",  "Quick Save (F7)"),
        ("quick_load",  "Quick Load (F9)"),
    ]

    def __init__(self, parent: QWidget, sound_config: dict, topmost: bool = False):
        super().__init__(parent)
        self.setWindowTitle("Sound Manager")
        self.setFixedSize(520, 430)
        self.sound_config = sound_config
        _set_icon(self)

        if topmost:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        sm_cfg = _load_window_config("sound_manager")
        if sm_cfg:
            self.move(sm_cfg["x"], sm_cfg["y"])
        else:
            _center_window(self, 520, 430)

        self._save_pos_timer = QTimer(self)
        self._save_pos_timer.setSingleShot(True)
        self._save_pos_timer.timeout.connect(self._persist_window_position)

        # MP3 list
        self.all_mp3s   = _collect_all_mp3s()
        self.mp3_labels = (
            ["(none)"]
            + list(_SPECIAL_SOUND_LABELS.values())
            + [_mp3_display_label(p) for p in self.all_mp3s]
        )
        self._mp3_offset = 1 + len(_SPECIAL_SOUND_LABELS)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # --- Mode selection ---
        mode_group  = QGroupBox("Sound Mode")
        mode_layout = QVBoxLayout(mode_group)
        self.mode_btn_group = QButtonGroup(self)

        rb_style = _RADIOBUTTON_STYLE

        for value, text in [
            ("random",  "🎲  Random  (fart on save actions · burp on load)"),
            ("classic", "🎵  Classic  (fx/save.mp3  ·  fx/load.mp3)"),
            ("custom",  "🎛   Custom assignment (choose a file per action)"),
        ]:
            rb = QRadioButton(text)
            rb.setProperty("mode_value", value)
            rb.setStyleSheet(rb_style)
            if sound_config.get("mode", "random") == value:
                rb.setChecked(True)
            self.mode_btn_group.addButton(rb)
            mode_layout.addWidget(rb)

        self.mode_btn_group.buttonClicked.connect(self._on_mode_change)
        layout.addWidget(mode_group)

        # --- Custom assignment ---
        self.custom_group = QGroupBox("Custom Sound Assignment")
        custom_layout     = QVBoxLayout(self.custom_group)
        self.combos       = {}
        self.preview_btns = {}

        for action, label in self.ACTIONS:
            row        = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)

            lbl = QLabel(label)
            lbl.setFixedWidth(145)
            row_layout.addWidget(lbl)

            current_path = sound_config.get(action)
            try:
                if current_path in _SPECIAL_SOUND_LABELS:
                    idx = self.mp3_labels.index(_SPECIAL_SOUND_LABELS[current_path])
                elif current_path in self.all_mp3s:
                    idx = self.all_mp3s.index(current_path) + self._mp3_offset
                else:
                    idx = 0
            except (ValueError, TypeError):
                idx = 0

            combo = QComboBox()
            combo.addItems(self.mp3_labels)
            combo.setCurrentIndex(idx)
            combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            row_layout.addWidget(combo)
            self.combos[action] = combo

            btn = QPushButton("▶")
            btn.setFixedWidth(32)
            btn.clicked.connect(lambda checked=False, a=action: self._preview(a))
            row_layout.addWidget(btn)
            self.preview_btns[action] = btn

            custom_layout.addWidget(row)

        layout.addWidget(self.custom_group)

        # --- Volume & Mute ---
        vol_group  = QGroupBox("Global Volume")
        vol_layout = QHBoxLayout(vol_group)

        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(int(sound_config.get("volume", 1.0) * 100))
        self.vol_slider.valueChanged.connect(self._on_volume_change)
        vol_layout.addWidget(self.vol_slider)

        self.vol_label = QLabel(f"{self.vol_slider.value()} %")
        self.vol_label.setFixedWidth(45)
        vol_layout.addWidget(self.vol_label)

        self.mute_check = QCheckBox("Mute")
        self.mute_check.setChecked(sound_config.get("mute", False))
        self.mute_check.setStyleSheet(_CHECKBOX_STYLE)
        vol_layout.addWidget(self.mute_check)

        layout.addWidget(vol_group)

        # --- Save / Cancel ---
        btn_row        = QWidget()
        btn_row_layout = QHBoxLayout(btn_row)
        btn_row_layout.setContentsMargins(0, 0, 0, 0)

        save_btn = QPushButton("Save")
        save_btn.setFixedWidth(100)
        save_btn.clicked.connect(self._save)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(100)
        cancel_btn.clicked.connect(self.reject)

        btn_row_layout.addStretch()
        btn_row_layout.addWidget(save_btn)
        btn_row_layout.addWidget(cancel_btn)
        btn_row_layout.addStretch()

        layout.addWidget(btn_row)

        self._on_mode_change()

    # ------------------------------------------------------------------

    def moveEvent(self, event):
        self._save_pos_timer.start(500)
        super().moveEvent(event)

    def _persist_window_position(self):
        _save_window_config("sound_manager", self.x(), self.y())

    def _get_current_mode(self) -> str:
        for btn in self.mode_btn_group.buttons():
            if btn.isChecked():
                return btn.property("mode_value")
        return "random"

    def _on_mode_change(self, _btn=None):
        is_custom = self._get_current_mode() == "custom"
        for action in self.combos:
            self.combos[action].setEnabled(is_custom)
            self.preview_btns[action].setEnabled(is_custom)

    def _on_volume_change(self, value: int):
        self.vol_label.setText(f"{value} %")

    def _preview(self, action: str):
        label = self.combos[action].currentText()
        if label == "(none)":
            return
        if label in _SPECIAL_SOUND_VALUES:
            sentinel = _SPECIAL_SOUND_VALUES[label]
            try:
                files = _get_fart_files() if sentinel == RANDOM_FART else _get_burp_files()
                if files:
                    _play_sound(random.choice(files), volume=self.vol_slider.value() / 100)
            except Exception as e:
                QMessageBox.critical(self, "Preview Error", str(e))
            return
        try:
            idx = self.mp3_labels.index(label) - self._mp3_offset
            _play_sound(self.all_mp3s[idx], volume=self.vol_slider.value() / 100)
        except Exception as e:
            QMessageBox.critical(self, "Preview Error", str(e))

    def _save(self):
        self.sound_config["mode"]   = self._get_current_mode()
        self.sound_config["volume"] = self.vol_slider.value() / 100
        self.sound_config["mute"]   = self.mute_check.isChecked()
        for action in self.combos:
            label = self.combos[action].currentText()
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
        self.accept()


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class SaveManagerUI(QMainWindow):

    # Signals used to marshal keyboard-thread callbacks → main thread
    _quickSaveSignal = Signal()
    _quickLoadSignal = Signal()

    def __init__(self):
        super().__init__()

        self.sound_config = _load_sound_config()

        self.setWindowTitle("Mewgenics Save Manager")
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        _set_icon(self)

        win_cfg = _load_window_config("main")
        if win_cfg:
            self.setGeometry(win_cfg["x"], win_cfg["y"], 520, 420)
        else:
            _center_window(self, 520, 420)

        self._save_pos_timer = QTimer(self)
        self._save_pos_timer.setSingleShot(True)
        self._save_pos_timer.timeout.connect(self._persist_window_position)

        # --- Central widget & layout ---
        central     = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(6)
        self.setCentralWidget(central)

        # Top button row
        btn_row    = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        self.save_button = QPushButton("Save Backup")
        self.save_button.setMinimumHeight(36)
        self.save_button.clicked.connect(self.create_named_backup)
        btn_layout.addWidget(self.save_button)

        self.quick_save_button = QPushButton("Quick Save (F7)")
        self.quick_save_button.setMinimumHeight(36)
        self.quick_save_button.clicked.connect(self.create_quick_save)
        btn_layout.addWidget(self.quick_save_button)

        self.quick_load_button = QPushButton("Quick Load (F9)")
        self.quick_load_button.setMinimumHeight(36)
        self.quick_load_button.clicked.connect(self.quick_load)
        btn_layout.addWidget(self.quick_load_button)

        main_layout.addWidget(btn_row)

        # Backup list
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(lambda _item: self.reload_backup())
        main_layout.addWidget(self.list_widget)

        # Action row
        action_row    = QWidget()
        action_layout = QHBoxLayout(action_row)
        action_layout.setContentsMargins(0, 0, 0, 0)

        self.reload_button = QPushButton("Reload Selected")
        self.reload_button.clicked.connect(self.reload_backup)
        action_layout.addWidget(self.reload_button)

        self.rename_button = QPushButton("Rename Selected")
        self.rename_button.clicked.connect(self.rename_backup)
        action_layout.addWidget(self.rename_button)

        self.export_button = QPushButton("Export Selected")
        self.export_button.clicked.connect(self.export_backup)
        action_layout.addWidget(self.export_button)

        self.clean_button = QPushButton("Clean Backups (keep 5)")
        self.clean_button.clicked.connect(self.clean_backups)
        action_layout.addWidget(self.clean_button)

        self.sound_manager_button = QPushButton("🔊 Sound Manager")
        self.sound_manager_button.clicked.connect(self.open_sound_manager)
        action_layout.addWidget(self.sound_manager_button)

        main_layout.addWidget(action_row)

        # Bottom row
        bottom_row    = QWidget()
        bottom_layout = QHBoxLayout(bottom_row)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        self.topmost_check = QCheckBox("Always on top")
        self.topmost_check.setChecked(True)
        self.topmost_check.stateChanged.connect(self._on_topmost_changed)
        self.topmost_check.setStyleSheet(_CHECKBOX_STYLE)
        bottom_layout.addWidget(self.topmost_check)

        bottom_layout.addStretch()

        # Moon / Sun theme toggle
        moon_lbl = QLabel("🌙")
        moon_lbl.setToolTip("Thème sombre")
        moon_lbl.setStyleSheet("font-size: 13px;")
        bottom_layout.addWidget(moon_lbl)

        self.theme_slider = QSlider(Qt.Orientation.Horizontal)
        self.theme_slider.setRange(0, 1)
        self.theme_slider.setFixedWidth(38)
        self.theme_slider.setToolTip("Thème sombre / clair")
        self.theme_slider.setValue(0 if _load_theme() == "dark" else 1)
        self.theme_slider.valueChanged.connect(self._on_theme_changed)
        bottom_layout.addWidget(self.theme_slider)

        sun_lbl = QLabel("☀️")
        sun_lbl.setToolTip("Thème clair")
        sun_lbl.setStyleSheet("font-size: 13px;")
        bottom_layout.addWidget(sun_lbl)

        bottom_layout.addSpacing(10)

        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setStyleSheet("color: gray; font-size: 9px;")
        bottom_layout.addWidget(version_label)

        main_layout.addWidget(bottom_row)

        # Global hotkeys (fire even when the app is not focused)
        self._quickSaveSignal.connect(self.create_quick_save)
        self._quickLoadSignal.connect(lambda: self.quick_load(confirm=False))
        keyboard.add_hotkey("F7", lambda: self._quickSaveSignal.emit())
        keyboard.add_hotkey("F9", lambda: self._quickLoadSignal.emit())

        self.refresh_list()
        self.show()

    # ------------------------------------------------------------------

    def moveEvent(self, event):
        self._save_pos_timer.start(500)
        super().moveEvent(event)

    def _persist_window_position(self):
        _save_window_config("main", self.x(), self.y())

    def _on_topmost_changed(self, state: int):
        topmost = state == Qt.CheckState.Checked.value
        self.setWindowFlag(Qt.WindowStaysOnTopHint, topmost)
        self.show()   # required to apply flag change

    def _on_theme_changed(self, value: int):
        theme = "light" if value == 1 else "dark"
        _save_theme(theme)
        app = QApplication.instance()
        if theme == "dark":
            _apply_dark_palette(app)
        else:
            _apply_light_palette(app)
        # Force re-evaluation of palette() references in stylesheets
        self.topmost_check.setStyleSheet("")
        self.topmost_check.setStyleSheet(_CHECKBOX_STYLE)

    # ------------------------------------------------------------------

    def open_sound_manager(self):
        dlg = SoundManagerDialog(
            self, self.sound_config,
            topmost=self.topmost_check.isChecked()
        )
        dlg.exec()
        _save_sound_config(self.sound_config)

    def _play_sound_for_action(self, action: str):
        if self.sound_config.get("mute", False):
            return
        mode   = self.sound_config.get("mode", "random")
        volume = self.sound_config.get("volume", 1.0)
        base   = _base_path()

        if mode == "random":
            if action in ("save_backup", "quick_save"):
                farts = _get_fart_files()
                if farts:
                    _play_sound(random.choice(farts), volume=volume)
            elif action == "quick_load":
                burps = _get_burp_files()
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
                farts = _get_fart_files()
                if farts:
                    _play_sound(random.choice(farts), volume=volume)
            elif path == RANDOM_BURP:
                burps = _get_burp_files()
                if burps:
                    _play_sound(random.choice(burps), volume=volume)
            elif path and os.path.exists(path):
                _play_sound(path, volume=volume)

    # ------------------------------------------------------------------

    def refresh_list(self):
        self.list_widget.clear()
        folders = [
            f for f in os.listdir(SPECIAL_BACKUP_FOLDER)
            if os.path.isdir(os.path.join(SPECIAL_BACKUP_FOLDER, f))
        ]
        folders.sort(
            key=lambda f: os.path.getctime(os.path.join(SPECIAL_BACKUP_FOLDER, f)),
            reverse=True,
        )
        for f in folders:
            path          = os.path.join(SPECIAL_BACKUP_FOLDER, f)
            creation_time = os.path.getctime(path)
            date_str      = datetime.fromtimestamp(creation_time).strftime("%d/%m/%y %H:%M:%S")
            self.list_widget.addItem(f"{date_str}   {f}")

    def quick_load(self, confirm: bool = True):
        if self.list_widget.count() == 0:
            QMessageBox.information(self, "Quick Load", "No backup available")
            return

        entry = self.list_widget.item(0).text()
        name  = entry.split("   ", 1)[1]

        folder      = os.path.join(SPECIAL_BACKUP_FOLDER, name)
        backup_file = os.path.join(folder, TARGET_FILE)

        if not os.path.exists(backup_file):
            QMessageBox.critical(self, "Error", "Backup file missing")
            return

        if confirm:
            answer = QMessageBox.question(
                self, "Quick Load",
                f"Load most recent backup '{name}' ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        create_restore_safety_backup()

        try:
            shutil.copy2(backup_file, TARGET_PATH)
            self._play_sound_for_action("quick_load")
            print(f"⚡ Quick loaded: {name}")
        except Exception as e:
            QMessageBox.critical(self, "Quick Load Error", str(e))
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
            QMessageBox.critical(self, "Quick Save Error", str(e))
            print(f"❌ Quick save failed: {e}")

        self.refresh_list()

    def create_named_backup(self):
        name, ok = QInputDialog.getText(self, "Backup Name", "Enter backup name:")
        if not ok or not name:
            return

        safe_name   = name.replace(" ", "_")
        folder_path = os.path.join(SPECIAL_BACKUP_FOLDER, safe_name)

        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

        os.makedirs(folder_path)
        backup_path = os.path.join(folder_path, TARGET_FILE)
        shutil.copy2(TARGET_PATH, backup_path)
        self._play_sound_for_action("save_backup")
        print(f"⭐ Named backup created: {safe_name}")

        self.refresh_list()

    def reload_backup(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.information(self, "Reload", "Select a backup first")
            return

        entry = item.text()
        name  = entry.split("   ", 1)[1]

        folder      = os.path.join(SPECIAL_BACKUP_FOLDER, name)
        backup_file = os.path.join(folder, TARGET_FILE)

        if not os.path.exists(backup_file):
            QMessageBox.critical(self, "Error", "Backup file missing")
            return

        answer = QMessageBox.question(
            self, "Confirm",
            f"Reload backup '{name}' ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        create_restore_safety_backup()
        shutil.copy2(backup_file, TARGET_PATH)
        print(f"🔄 Reloaded backup: {name}")

    def rename_backup(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.information(self, "Rename", "Select a backup first")
            return

        entry    = item.text()
        old_name = entry.split("   ", 1)[1]
        old_path = os.path.join(SPECIAL_BACKUP_FOLDER, old_name)

        new_name, ok = QInputDialog.getText(
            self, "Rename Backup", "New name:", text=old_name
        )
        if not ok or not new_name.strip():
            return

        safe_name = new_name.strip().replace(" ", "_")
        new_path  = os.path.join(SPECIAL_BACKUP_FOLDER, safe_name)

        if safe_name == old_name:
            return

        if os.path.exists(new_path):
            QMessageBox.warning(
                self, "Rename",
                f"A backup named '{safe_name}' already exists."
            )
            return

        try:
            os.rename(old_path, new_path)
            print(f"✏️  Renamed '{old_name}' → '{safe_name}'")
        except Exception as e:
            QMessageBox.critical(self, "Rename Error", str(e))
            return

        self.refresh_list()

    def export_backup(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.information(self, "Export", "Select a backup first")
            return

        entry = item.text()
        name  = entry.split("   ", 1)[1]

        folder      = os.path.join(SPECIAL_BACKUP_FOLDER, name)
        backup_file = os.path.join(folder, TARGET_FILE)

        if not os.path.exists(backup_file):
            QMessageBox.critical(self, "Error", "Backup file missing")
            return

        dest, _ = QFileDialog.getSaveFileName(
            self,
            "Export Backup",
            os.path.join(os.path.expanduser("~"), TARGET_FILE),
            "Save files (*.sav);;All files (*.*)",
        )
        if not dest:
            return

        try:
            shutil.copy2(backup_file, dest)
            QMessageBox.information(self, "Export", f"Backup exported to:\n{dest}")
            print(f"📤 Exported '{name}' → {dest}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))
            print(f"❌ Export failed: {e}")

    def clean_backups(self):
        folders = [
            f for f in os.listdir(SPECIAL_BACKUP_FOLDER)
            if os.path.isdir(os.path.join(SPECIAL_BACKUP_FOLDER, f))
        ]
        folders.sort(
            key=lambda f: os.path.getctime(os.path.join(SPECIAL_BACKUP_FOLDER, f)),
            reverse=True,
        )
        to_delete = folders[5:]

        safety_files = [
            f for f in os.listdir(SAFETY_FOLDER)
            if os.path.isfile(os.path.join(SAFETY_FOLDER, f))
        ]
        safety_files.sort(
            key=lambda f: os.path.getctime(os.path.join(SAFETY_FOLDER, f)),
            reverse=True,
        )
        safety_to_delete = safety_files[5:]

        if not to_delete and not safety_to_delete:
            QMessageBox.information(
                self, "Clean Backups", "Nothing to delete (5 or fewer backups)"
            )
            return

        answer = QMessageBox.question(
            self, "Clean Backups",
            f"Delete {len(to_delete)} backup(s) and {len(safety_to_delete)} safety backup(s),"
            f" keeping the 5 most recent of each ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        for f in to_delete:
            shutil.rmtree(os.path.join(SPECIAL_BACKUP_FOLDER, f))
            print(f"🗑 Deleted backup: {f}")

        for f in safety_to_delete:
            os.remove(os.path.join(SAFETY_FOLDER, f))
            print(f"🗑 Deleted safety backup: {f}")

        self.refresh_list()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    if _load_theme() == "light":
        _apply_light_palette(app)
    else:
        _apply_dark_palette(app)
    ui = SaveManagerUI()
    sys.exit(app.exec())
