#!/usr/bin/env python3
import json
import os
import sys

def main():
    flavor = os.environ.get("FLAVOR", "stable")
    version = os.environ.get("VERSION", "32.56")
    version_code = int(os.environ.get("VERSION_CODE", "2446"))
    target_tag = os.environ.get("TARGET_TAG", f"v{version}-shorts-slider")
    json_file = os.environ.get("JSON_FILE", f"smarttube_{flavor}2.json")
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
                "Up/Down remote D-pad navigation for endless Shorts scrolling",
                "Continuous queue background prefetching",
                "ExoPlayer instant playback start buffer set to 500ms",
                f"Official upstream base {version}"
            ],
            "changelog_fr": [
                f"Édition SmartTube Shorts Slider {type_label}",
                "Navigation fluide Haut/Bas sur télécommande pour défilement infini des Shorts",
                "Préchargement automatique de la file d'attente en arrière-plan",
                "Démarrage quasi-instantané du lecteur (tampon réduit à 500ms)",
                f"Base officielle {version}"
            ]
        }
    }

    json_path = os.path.join("release_assets", json_file)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(ota_data, f, indent=4, ensure_ascii=False)
    print(f"✅ Generated OTA update JSON: {json_path}")

    # 2. Generate Release Notes Markdown
    notes = f"""### 🚀 SmartTube Shorts Slider {type_label} Edition

Ce fork officiel de SmartTube intègre le **défilement vertical infini des Shorts** sur télécommande TV et le préchargement instantané des vidéos.

#### ✨ Nouveautés exclusives / Highlights
- 🎮 **Navigation Télécommande Haut / Bas** : Défilement fluide des Shorts comme sur smartphone / TikTok.
- 🔄 **Préchargement Automatique du Short Suivant** : Le short suivant est déjà chargé en tâche de fond.
- ⏯️ **Bouton Défilement Automatique (Auto-Scroll)** : Active/désactive l'enchaînement automatique des Shorts.
- ♾️ **File d'attente continue (10 à 20 Shorts d'avance)** : Défilement infini garanti sans fin de liste.

#### 📱 APKs disponibles ci-dessous :
- `SmartTube_Shorts_Slider_{flavor}_{version}_armeabi-v7a.apk` : **Recommandé pour Amazon Fire TV Stick**, Mi Box et la majorité des clés TV.
- `SmartTube_Shorts_Slider_{flavor}_{version}_arm64-v8a.apk` : **NVIDIA Shield TV** et box TV 64-bit récentes.
- `SmartTube_Shorts_Slider_{flavor}_{version}_universal.apk` : Version tout-en-un universelle.
- `SmartTube_Shorts_Slider_{flavor}_{version}_x86.apk` : Émulateurs PC & architectures Intel.
"""

    with open("release_notes.md", "w", encoding="utf-8") as f:
        f.write(notes)
    print("✅ Generated Release Notes: release_notes.md")

if __name__ == "__main__":
    main()
