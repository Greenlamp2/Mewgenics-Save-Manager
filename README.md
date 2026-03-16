# 💩 Mewgenics Save Manager

A save file manager for the game **Mewgenics** (Glaiel Games).  
It automatically detects your Steam save file and lets you create, load, rename, and clean up backups in one click — or even from within the game using global keyboard shortcuts.

---

## ✨ Features

### 💾 Save Management
- **Save Backup**: manually creates a named backup (custom name).
- **Quick Save (F7)**: instantly creates a timestamped backup named `quicksave_YYYYMMDD_HHMMSS`.
- **Quick Load (F9)**: loads the most recent backup in the list.
- **Reload Selected**: loads the selected backup from the list (with confirmation).
- **Rename Selected**: renames an existing backup.
- **Double-click** on a backup: equivalent to clicking *Reload Selected*.
- **Clean Backups (keep 5)**: deletes all backups except the 5 most recent ones, including safety backups.
- **Safety backup**: before any reload, an automatic safety copy is created in the `restore_safety/` folder.

### ⌨️ Global Keyboard Shortcuts
- **F7**: Quick Save — works even when the application is not in focus (e.g. while playing).
- **F9**: Quick Load — same, with no confirmation dialog.

### 🔊 Sound Manager
- **Random Mode**: plays a random fart sound (`fx/fart/`) on save, and a random burp (`fx/burp/`) on load.
- **Classic Mode**: plays `fx/save.mp3` and `fx/load.mp3`.
- **Custom Mode**: assigns a specific sound to each action (*Save Backup*, *Quick Save*, *Quick Load*), with the option to select "All Farts (random)" or "All Burps (random)".
- **Preview**: ▶ button to test a sound directly in the Sound Manager.
- **Global Volume**: slider from 0 to 100%.
- **Mute**: silences all sounds in one click.
- Sounds are only played **on success** of the operation.

### 🎵 Custom Sounds
- Built-in sounds are located in `fx/fart/`, `fx/burp/`, `fx/save.mp3`, `fx/load.mp3`.
- Place your own MP3 files in an `fx/` folder next to the executable to add them to the list.
- Sound configuration is saved and restored on next launch.

### 🎨 Themes
- **Dark theme** (default) and **light theme** (classic Windows style).
- Toggle via a 🌙 / ☀️ slider at the bottom of the window.
- Theme choice is remembered between sessions.

### 🪟 Interface
- **Always on Top**: checkbox to keep the window always in the foreground.
- **Window position remembered**: the position of the main window and the Sound Manager is saved.
- **Auto-centered** on first launch.
- Custom 💩 icon in the title bar and taskbar.

---

## 📁 Save File Structure

Backups are stored in:
```
%APPDATA%\Glaiel Games\Mewgenics\<SteamID>\saves\custom\
    named_backups\   ← your backups (named and quick saves)
    restore_safety\  ← automatic safety backups
    sound_config.json
    window_config.json
```

The monitored save file is:
```
%APPDATA%\Glaiel Games\Mewgenics\<SteamID>\saves\steamcampaign01.sav
```

---

## 🚀 Installation (from source)

**Requirements:** Python 3.13+

```bash
pip install -r requirements.txt
python main.py
```

---

## 🎮 Quick Start

1. Launch the app (or the EXE).
2. Your save file is detected automatically.
3. Press **F7** from within the game to create a Quick Save.
4. Press **F9** from within the game to load the latest Quick Save.
5. Manage your backups from the UI: rename, reload, clean…
