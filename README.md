# SmartTube Shorts Slider Edition

[<img src="images/badge_github.png" alt="Get it on GitHub" height="80">](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases/latest)

[![Release](https://img.shields.io/github/v/release/valoche-68/SmartTube-Shorts-Slider?label=Latest%20Release&color=blue)](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases/latest)
[![Build & Release](https://github.com/valoche-68/SmartTube-Shorts-Slider/actions/workflows/release-shorts-slider.yml/badge.svg)](https://github.com/valoche-68/SmartTube-Shorts-Slider/actions/workflows/release-shorts-slider.yml)
[![License](https://img.shields.io/github/license/valoche-68/SmartTube-Shorts-Slider)](LICENSE)

> [!TIP]
> 🇫🇷 **[Cliquez ici pour lire la documentation en Français](#-version-française)**

SmartTube **Shorts Slider** is an enhanced fork of the original [SmartTube by Yurii Liskov](https://github.com/yuliskov/SmartTube). It is designed specifically to provide a **smooth, continuous, smartphone-like experience for YouTube Shorts on Android TV and Amazon Fire TV**, utilizing simple remote control Up/Down arrows.

---

## 🚀 Key Features (Shorts Slider Edition)

- 🎮 **Up / Down Remote D-Pad Navigation**: Seamlessly navigate between YouTube Shorts using the Up and Down keys on your TV remote control, just like scrolling through TikTok or YouTube Shorts on mobile.
- 🔄 **New Auto-Scroll Toggle Button**: A dedicated button in player controls to enable or disable automatic hands-free scrolling to the next Short when the current one finishes. Persistently saved across sessions.
- ♾️ **Eager 10 to 20 Shorts Queue Prefetching**: Automatically maintains a continuous buffer of 10 to 20 Shorts ahead in the queue so the feed never interrupts or ends.
- 🔄 **Automatic Next-Short Preloading**: While you are watching a Short, the next video is automatically fetched and prepared in the background for a seamless transition.
- 📡 **Over-the-Air (OTA) Updates**: The app checks for and installs updates directly from this repository's releases.

---

## 📥 Download APKs (v32.56 Stable)

Choose the APK matching your TV hardware:

| Architecture | Recommended Devices | Direct Download Link |
| :--- | :--- | :---: |
| **`armeabi-v7a`** | **Amazon Fire TV Stick** (Lite, HD, 4K), Xiaomi Mi Box, most 32-bit Android TVs | [Download APK](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases/latest/download/SmartTube_stable_32.56_armeabi-v7a.apk) |
| **`arm64-v8a`** | **NVIDIA Shield TV**, modern 64-bit Android TVs & Google TVs | [Download APK](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases/latest/download/SmartTube_stable_32.56_arm64-v8a.apk) |
| **`universal`** | All-in-one package (contains all architectures, ~38 MB) | [Download APK](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases/latest/download/SmartTube_stable_32.56_universal.apk) |
| **`x86`** | PC Emulators, Android-x86, Intel devices | [Download APK](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases/latest/download/SmartTube_stable_32.56_x86.apk) |

---

## 📊 Hardware Benchmark & Latency (Fire TV Stick)

> [!NOTE]  
> Benchmark details on an **Amazon Fire TV Stick**:
> - **First Short Launch (Cold Start)**: When opening a Short right after launching the application, expect a normal initial buffering delay of **2 to 4 seconds** (network connection establishment, initial video codec allocation, and YouTube DASH handshake).
> - **Subsequent Shorts Transitions**: Once inside playback, because each Short is played while the next Short is already loaded in the background, transitions between consecutive Shorts become smooth and seamless.

### How background loading works on TV hardware:

1. **Continuous Next-Short Loading**:  
   As soon as a Short starts playing, the application immediately requests the stream URLs and formats for the upcoming Short in the background.
2. **Buffer Tuned to 500 ms**:  
   The video starts decoding as soon as 0.5s of data is buffered, minimizing wait time while maintaining smooth playback.
3. **Continuous 10-20 Queue Prefetch**:  
   The application always keeps 10 to 20 Shorts ready in memory, avoiding any pause or shelf end.
4. **Hardware Decoder Limits Handled**:  
   On TV sticks with 1 GB of RAM, running dual concurrent decoders causes memory crashes. Our eager pipeline feeds the single hardware decoder ahead of time, extracting the highest possible performance without stability risks.

---

## 🔄 Migration Guide: Keeping Your Settings & Accounts

Because this fork is signed with a dedicated release key and the official app is signed with Yurii Liskov's private key, Android does not allow installing one over the other directly without first migrating your data.

### Method 1: 100% on TV with Remote Control (No PC required)

1. Open your current SmartTube app on TV.
2. Go to **Settings > General > Backup data** (this saves your accounts, subscriptions, history, and settings to the TV's internal storage at `/sdcard/data/org.smarttube.stable/Backup/`).
3. Uninstall the previous SmartTube app from the Fire TV / Android TV app settings. (*Note: Your backup file remains safe in storage!*)
4. Open the **Downloader** app on your TV and install the new APK from the download table above.
5. Launch the new SmartTube app and go to **Settings > General > Restore data**.
6. Everything is restored instantly! All future updates will install automatically.

---

### Method 2: Via ADB (Command Line)

```bash
# 1. Connect to your TV
adb connect <TV_IP_ADDRESS>:5555

# 2. Backup current settings (optional local copy)
adb pull /sdcard/data/org.smarttube.stable/Backup /tmp/smarttube_backup

# 3. Uninstall previous version
adb uninstall org.smarttube.stable

# 4. Install the new Shorts Slider APK
adb install -r SmartTube_stable_32.56_armeabi-v7a.apk

# 5. Restore settings on the TV
# Open SmartTube -> Settings -> General -> Restore data
```

---

### 🤖 AI Prompt for Automated Migration via ADB

If you use an AI coding assistant (such as Antigravity, Claude, or ChatGPT) connected to your terminal, copy-paste this prompt:

```text
Please help me migrate my SmartTube installation on my Android TV (IP: <YOUR_TV_IP>) to the new SmartTube-Shorts-Slider build without losing any data.
1. Connect via ADB to <YOUR_TV_IP>:5555.
2. Verify that a backup exists in /sdcard/data/org.smarttube.stable/Backup. If not, trigger a backup or pull shared_prefs.
3. Pull a copy of the backup to my computer as a safety measure.
4. Uninstall the existing package org.smarttube.stable.
5. Install the new SmartTube_stable_32.56_armeabi-v7a.apk.
6. Grant storage permissions if needed (READ_EXTERNAL_STORAGE).
7. Start the application activity and verify it launches correctly so I can restore my settings.
```

---

<br>

---

# 🇫🇷 Version Française

SmartTube **Shorts Slider** est une version améliorée du célèbre client YouTube pour téléviseurs [SmartTube](https://github.com/yuliskov/SmartTube). Ce fork apporte une **expérience fluide et continue pour la lecture des YouTube Shorts sur Android TV et Fire TV Stick**, grâce aux flèches Haut et Bas de votre télécommande.

---

### 🌟 Fonctionnalités Exclusives (Shorts Slider)

- 🎮 **Navigation Haut / Bas à la télécommande** : Faites défiler les Shorts simplement avec les flèches Haut/Bas, comme sur TikTok ou l'application mobile.
- 🔄 **Nouveau Bouton Défilement Automatique (Auto-Scroll)** : Un bouton dédié dans les contrôles du lecteur permet d'activer ou désactiver l'enchaînement automatique des Shorts sans toucher à la télécommande. Sauvegardé automatiquement dans vos préférences.
- ♾️ **File d'Attente Continue (10 à 20 Shorts d'avance)** : L'application précharge en continu une réserve de 10 à 20 Shorts d'avance pour garantir un flux infini sans interruption.
- 🔄 **Préchargement Automatique du Short Suivant** : Pendant que vous regardez une vidéo, le Short suivant est déjà chargé en arrière-plan pour s'enchaîner de manière fluide.
- 📡 **Mises à jour automatiques OTA** : L'application vous avertit et se met à jour directement depuis les releases de ce dépôt.

---

### 📥 Téléchargements des APKs (Version 32.56 Stable)

Choisissez l'APK adapté au matériel de votre téléviseur :

| Architecture | Périphériques Recommandés | Lien de Téléchargement Direct |
| :--- | :--- | :---: |
| **`armeabi-v7a`** | **Amazon Fire TV Stick** (Lite, HD, 4K), Xiaomi Mi Box, majorité des clés TV 32-bit | [Télécharger l'APK](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases/latest/download/SmartTube_stable_32.56_armeabi-v7a.apk) |
| **`arm64-v8a`** | **NVIDIA Shield TV**, box TV et téléviseurs 64-bit récents | [Télécharger l'APK](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases/latest/download/SmartTube_stable_32.56_arm64-v8a.apk) |
| **`universal`** | Version tout-en-un (contient toutes les architectures, ~38 Mo) | [Télécharger l'APK](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases/latest/download/SmartTube_stable_32.56_universal.apk) |
| **`x86`** | Émulateurs PC / Android-x86 / Processeurs Intel | [Télécharger l'APK](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases/latest/download/SmartTube_stable_32.56_x86.apk) |

---

### ⏱️ Analyse Technique & Benchmark sur Fire TV

> [!NOTE]  
> Détails mesurés sur **Amazon Fire TV Stick** :
> - **Lancement du premier Short (Démarrage à froid)** : Lors du clic sur un premier Short juste après avoir ouvert l'application, un délai d'initialisation normal de **2 à 4 secondes** est présent (connexion réseau, handshake YouTube DASH et initialisation du décodeur matériel vidéo).
> - **Transitions entre les Shorts suivants** : Une fois dans le lecteur, comme chaque Short est lu pendant que le Short suivant est déjà chargé en tâche de fond, le passage d'une vidéo à l'autre s'effectue de manière fluide et directe.

#### Comment fonctionne le chargement anticipé sur clé TV ?
1. **Préchargement systématique du Short suivant** :  
   Dès qu'un Short commence, l'application extrait immédiatement les formats et liens du Short suivant en arrière-plan.
2. **Tampon ExoPlayer réglé à 500 ms** :  
   Le décodage démarre dès qu'une demi-seconde de flux est en mémoire vive.
3. **Réserve permanente de 10 à 20 vidéos** :  
   L'application anticipe en permanence la suite de la liste de lecture.
4. **Optimisation sans surcharger la mémoire** :  
   Sur une clé TV dotée de seulement 1 Go de RAM, ouvrir plusieurs lecteurs vidéo en même temps ferait planter l'appareil. Ce pipeline alimente le décodeur matériel existant de façon optimale et sans aucun risque d'instabilité.

---

### 🔄 Guide de Migration (Conserver 100% de ses données et comptes)

Les signatures officielles de SmartTube et de ce fork étant différentes pour des raisons de sécurité cryptographique, il est nécessaire de transférer vos données lors du premier passage.

#### Méthode 1 : Directement sur la TV avec la télécommande (Sans PC)
1. Ouvrez votre SmartTube actuel sur votre TV.
2. Allez dans **Paramètres > Général > Sauvegarder les données**.
3. Désinstallez l'ancienne application SmartTube (le fichier de sauvegarde reste présent dans le stockage de la TV).
4. Ouvrez l'application **Downloader** sur votre TV et installez l'APK correspondant à votre appareil (lien ci-dessus).
5. Ouvrez le nouveau SmartTube et allez dans **Paramètres > Général > Restaurer les données**.
6. Vous retrouvez instantanément tous vos comptes, abonnements, favoris et historique !

#### Méthode 2 : Via ADB (Ligne de commande)
```bash
adb connect <IP_DE_VOTRE_TV>:5555
adb pull /sdcard/data/org.smarttube.stable/Backup /tmp/smarttube_backup
adb uninstall org.smarttube.stable
adb install -r SmartTube_stable_32.56_armeabi-v7a.apk
```
*Ouvrez ensuite l'application sur la TV et cliquez sur "Restaurer les données".*

---

## 🛠️ Build & Development

```bash
# Clone the repository
git clone https://github.com/valoche-68/SmartTube-Shorts-Slider.git
cd SmartTube-Shorts-Slider

# Configure signing properties (optional for release build)
echo "storeFile=/path/to/smarttube-release.jks" > keystore.properties
echo "storePassword=your_password" >> keystore.properties
echo "keyAlias=smarttube" >> keystore.properties
echo "keyPassword=your_password" >> keystore.properties

# Build Release APKs
./gradlew assembleStstableRelease
```

---

## 📄 License & Credits

- SmartTube is licensed under [GNU GPL v3.0](LICENSE).
- Original creator and maintainer: [Yurii Liskov (yuliskov)](https://github.com/yuliskov/SmartTube).
- Shorts Slider Edition maintained by [valoche-68](https://github.com/valoche-68).
