# 🛠️ Toolbox Pro

![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-blueviolet.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Repo Size](https://img.shields.io/github/repo-size/Zeemoud/Toolbox)

Une suite logicielle tout-en-un développée en **Python** avec **PyQt6**. Cette boîte à outils regroupe des fonctionnalités essentielles allant du téléchargement multimédia à la sécurité, le tout dans une interface moderne et personnalisable.

---

## 🚀 Fonctionnalités principales

### 📥 YouTube Downloader
* Téléchargement de vidéos (MP4) et d'audios (MP3).
* Support de la haute résolution (jusqu'en 4K) et du haut débit audio (320kbps).
* Gestion des files d'attente et barre de progression en temps réel.
* Intégration de **FFmpeg** pour une conversion parfaite.

### 🎨 Interface & Personnalisation
* **Thème Dynamique** : Switch instantané entre mode **Sombre** et mode **Clair**.
* Design moderne et épuré optimisé pour Windows.

### 🧰 Autres Outils inclus
* **Sécurité** : Générateur de mots de passe complexes.
* **Media** : Éditeur de métadonnées, Générateur de QR Code, Sélecteur de couleurs.
* **Utilitaires** : Traducteur, Convertisseur de fichiers, Calculatrice, Horloge et Météo.
* **Code** : Convertisseur de texte en code Morse.

---

## 📦 Installation

### Pour les utilisateurs (Windows)
Le plus simple est d'utiliser l'installeur officiel :
1. Allez dans la section [Releases](https://github.com/Zeemoud/Toolbox/releases).
2. Téléchargez `toolbox-setup.exe`.
3. Lancez l'installation et profitez !

### Pour les développeurs (Lancement via le code)
Si vous souhaitez modifier le code ou le lancer manuellement :
1. Clonez le dépôt : `git clone https://github.com/Zeemoud/Toolbox.git`
2. Installez les dépendances : `pip install -r requirements.txt` (n'oubliez pas d'installer ffmpeg sur votre système).
3. Lancez l'application : `python main.py`

---

## 🛠️ Technologies utilisées
* **Langage** : Python 3.11+
* **GUI** : PyQt6
* **Core** : yt-dlp, requests, qrcode, etc.
* **Packaging** : PyInstaller & Inno Setup

---

## 👤 Auteur
Développé par **Zeemoud**.
