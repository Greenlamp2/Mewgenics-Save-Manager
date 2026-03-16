# 💩 Mewgenics Save Manager

Un gestionnaire de sauvegardes pour le jeu **Mewgenics** (Glaiel Games).  
Il détecte automatiquement votre fichier de sauvegarde Steam et vous permet de créer, charger, renommer et nettoyer vos backups en un clic — ou même depuis le jeu grâce aux raccourcis clavier globaux.
---

## ✨ Fonctionnalités

### 💾 Gestion des sauvegardes
- **Save Backup** : crée une sauvegarde nommée manuellement (nom personnalisé).
- **Quick Save (F7)** : crée instantanément une sauvegarde horodatée nommée `quicksave_YYYYMMDD_HHMMSS`.
- **Quick Load (F9)** : charge la sauvegarde la plus récente de la liste.
- **Reload Selected** : charge la sauvegarde sélectionnée dans la liste (avec confirmation).
- **Rename Selected** : renomme une sauvegarde existante.
- **Double-clic** sur une sauvegarde : équivalent au bouton *Reload Selected*.
- **Clean Backups (keep 5)** : supprime toutes les sauvegardes sauf les 5 plus récentes, y compris les sauvegardes de sécurité.
- **Safety backup** : avant tout rechargement, une copie de sécurité automatique est créée dans le dossier `restore_safety/`.

### ⌨️ Raccourcis clavier globaux
- **F7** : Quick Save — fonctionne même quand l'application n'est pas au premier plan (ex. : pendant une partie).
- **F9** : Quick Load — idem, sans fenêtre de confirmation.

### 🔊 Gestionnaire de sons (Sound Manager)
- **Mode Aléatoire** : joue un pet aléatoire (`fx/fart/`) lors des sauvegardes, un rot aléatoire (`fx/burp/`) lors des chargements.
- **Mode Classique** : joue `fx/save.mp3` et `fx/load.mp3`.
- **Mode Personnalisé** : assigne un son précis à chaque action (*Save Backup*, *Quick Save*, *Quick Load*), avec possibilité de choisir « Tous les farts (aléatoire) » ou « Tous les burps (aléatoire) ».
- **Prévisualisation** : bouton ▶ pour tester un son directement dans le Sound Manager.
- **Volume global** : slider de 0 à 100 %.
- **Mute** : coupe tous les sons en un clic.
- Les sons ne sont joués **qu'en cas de succès** de l'opération.

### 🎵 Sons personnalisables
- Les MP3 embarqués sont dans `fx/fart/`, `fx/burp/`, `fx/save.mp3`, `fx/load.mp3`.
- Placez vos propres MP3 dans un dossier `fx/` à côté de l'exécutable pour les ajouter à la liste.
- La configuration des sons est sauvegardée et restaurée au prochain lancement.

### 🎨 Thèmes
- **Thème sombre** (défaut) et **thème clair** (style Windows classique).
- Bascule via un slider 🌙 / ☀️ dans le bas de la fenêtre.
- Le choix de thème est mémorisé entre les sessions.

### 🪟 Interface
- **Always on Top** : checkbox pour garder la fenêtre toujours au premier plan.
- **Position des fenêtres mémorisée** : la position de la fenêtre principale et du Sound Manager est sauvegardée.
- **Centrage automatique** au premier lancement.
- Icône personnalisée 💩 dans la barre de titre et le gestionnaire de tâches.

---

## 📁 Structure des sauvegardes

Les sauvegardes sont stockées dans :
```
%APPDATA%\Glaiel Games\Mewgenics\<SteamID>\saves\custom\
    named_backups\   ← vos sauvegardes (nommées et quick saves)
    restore_safety\  ← sauvegardes de sécurité automatiques
    sound_config.json
    window_config.json
```

Le fichier surveillé est :
```
%APPDATA%\Glaiel Games\Mewgenics\<SteamID>\saves\steamcampaign01.sav
```

---

## 🚀 Installation (depuis les sources)

**Prérequis :** Python 3.13+

```bash
pip install -r requirements.txt
python main.py
```
---

## 🎮 Utilisation rapide

1. Lancez l'application (ou l'EXE).
2. Votre sauvegarde est détectée automatiquement.
3. Utilisez **F7** depuis le jeu pour créer un Quick Save.
4. Utilisez **F9** depuis le jeu pour charger le dernier Quick Save.
5. Gérez vos sauvegardes depuis l'interface : rename, reload, clean…
