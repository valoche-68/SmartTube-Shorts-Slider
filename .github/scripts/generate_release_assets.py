#!/usr/bin/env python3
import json
import os
import sys

def main():
    flavor = os.environ.get("FLAVOR", "stable")
    version = os.environ.get("VERSION", "32.56")
    version_code = int(os.environ.get("VERSION_CODE", "2446"))
    target_tag = os.environ.get("TARGET_TAG", f"v{version}-shorts-slider")
    json_file = os.environ.get("JSON_FILE", f"smarttube_{flavor}.json")
    repo = os.environ.get("GITHUB_REPO", "valoche-68/SmartTube-Shorts-Slider")
    type_label = os.environ.get("TYPE_LABEL", "Stable")

    os.makedirs("release_assets", exist_ok=True)

    # 1. Generate OTA update JSON
    ota_data = {
        "package": {
            "downloadUrlList": [
                f"https://github.com/{repo}/releases/download/{target_tag}/SmartTube_Shorts_Slider_{flavor}_{version}_armeabi-v7a.apk"
            ],
            "downloadUrlList_arm64-v8a": [
                f"https://github.com/{repo}/releases/download/{target_tag}/SmartTube_Shorts_Slider_{flavor}_{version}_arm64-v8a.apk"
            ],
            "downloadUrlList_x86": [
                f"https://github.com/{repo}/releases/download/{target_tag}/SmartTube_Shorts_Slider_{flavor}_{version}_x86.apk"
            ]
        },
        version: {
            "versionCode": version_code,
            "changelog": [
                f"SmartTube Shorts Slider {type_label} Edition",
                f"Based on official SmartTube v{version} with addition of:",
                "• Up/Down remote D-pad navigation for endless Shorts scrolling",
                "• Automatic next-short preloading in background",
                "• Persistent player control toggle for Shorts Auto-Scroll",
                "• Continuous queue (10 to 20 Shorts ahead)"
            ],
            "changelog_fr": [
                f"Édition SmartTube Shorts Slider {type_label}",
                f"Sur la base de SmartTube officiel en version {version} avec ajout de :",
                "• Navigation fluide Haut/Bas sur télécommande pour défilement infini des Shorts",
                "• Préchargement automatique du Short suivant en arrière-plan",
                "• Bouton Défilement Automatique (Auto-Scroll) dans le lecteur",
                "• File d'attente continue (10 à 20 Shorts d'avance)"
            ]
        }
    }

    json_path = os.path.join("release_assets", json_file)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(ota_data, f, indent=4, ensure_ascii=False)
    print(f"✅ Generated OTA update JSON: {json_path}")

    root_json_path = f"smarttube_{flavor}.json"
    with open(root_json_path, "w", encoding="utf-8") as f:
        json.dump(ota_data, f, indent=4, ensure_ascii=False)
    print(f"✅ Synced root JSON: {root_json_path}")

    # 2. Generate Release Notes Markdown (Bilingual English / Français)
    type_en = "Beta (Pre-release)" if flavor == "beta" else "Stable"
    type_fr = "Bêta (Pre-release)" if flavor == "beta" else "Stable"

    notes = f"""### 🚀 SmartTube Shorts Slider v{version} {type_en}

---

### 🇬🇧 English

Based on official SmartTube v{version} with addition of:
- 🎮 **Up / Down Remote D-Pad Navigation**: Seamlessly navigate YouTube Shorts using the Up and Down keys on your TV remote control, just like mobile / TikTok.
- 🔄 **Automatic Next-Short Preloading**: While watching a Short, the next video format and stream URLs are automatically prepared in the background for instant transitions.
- ⏯️ **Auto-Scroll Toggle Button**: A dedicated player control button to enable or disable automatic hands-free scrolling when the current Short finishes.
- ♾️ **Continuous Queue (10 to 20 Shorts Ahead)**: Maintains a continuous buffer of 10 to 20 Shorts in memory so your feed never interrupts.

#### 📱 APK Download Guide
- `SmartTube_Shorts_Slider_{flavor}_{version}_armeabi-v7a.apk`: **Recommended for Amazon Fire TV Stick** (Lite, HD, 4K), Xiaomi Mi Box, and 32-bit Android TVs.
- `SmartTube_Shorts_Slider_{flavor}_{version}_arm64-v8a.apk`: **NVIDIA Shield TV**, modern 64-bit Android TVs and Google TVs.
- `SmartTube_Shorts_Slider_{flavor}_{version}_universal.apk`: All-in-one package for all architectures.
- `SmartTube_Shorts_Slider_{flavor}_{version}_x86.apk`: PC Emulators & Intel-based architectures.

---

### 🇫🇷 Version Française

Sur la base de SmartTube officiel en version {version} avec ajout de :
- 🎮 **Navigation Télécommande Haut / Bas** : Défilement fluide des Shorts avec les touches Haut et Bas de la télécommande, comme sur smartphone / TikTok.
- 🔄 **Préchargement Automatique du Short Suivant** : Pendant la lecture d'un Short, le format et les flux de la vidéo suivante sont déjà préparés en tâche de fond.
- ⏯️ **Bouton Défilement Automatique (Auto-Scroll)** : Bouton dédié dans l'interface du lecteur permettant d'activer ou désactiver l'enchaînement automatique sans toucher à la télécommande.
- ♾️ **File d'attente continue (10 à 20 Shorts d'avance)** : Réserve continue de 10 à 20 vidéos en mémoire pour un flux infini garanti sans fin de liste.

#### 📱 Guide de choix des APKs
- `SmartTube_Shorts_Slider_{flavor}_{version}_armeabi-v7a.apk` : **Recommandé pour Amazon Fire TV Stick**, Mi Box et majorité des clés TV 32-bit.
- `SmartTube_Shorts_Slider_{flavor}_{version}_arm64-v8a.apk` : **NVIDIA Shield TV** et téléviseurs 64-bit récents.
- `SmartTube_Shorts_Slider_{flavor}_{version}_universal.apk` : Version tout-en-un universelle.
- `SmartTube_Shorts_Slider_{flavor}_{version}_x86.apk` : Émulateurs PC & architectures Intel.
"""

    with open("release_notes.md", "w", encoding="utf-8") as f:
        f.write(notes)
    print("✅ Generated Release Notes: release_notes.md")

    # 3. Update README.md ONLY for Stable channel
    if flavor == "stable":
        update_readme(version)

def update_readme(version):
    readme_path = "README.md"
    if not os.path.exists(readme_path):
        return
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    import re
    # Replace version in English and French titles
    content = re.sub(r"## 📥 Download APKs \(v[0-9.]+ Stable\)", f"## 📥 Download APKs (v{version} Stable)", content)
    content = re.sub(r"## 📥 Téléchargements des APKs \(Version [0-9.]+ Stable\)", f"## 📥 Téléchargements des APKs (Version {version} Stable)", content)

    # Replace APK filenames in links and commands
    content = re.sub(r"SmartTube_Shorts_Slider_stable_[0-9.]+", f"SmartTube_Shorts_Slider_stable_{version}", content)

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ README.md updated with Stable version {version}")

if __name__ == "__main__":
    main()
