# Installer Shorts Slider depuis un PC

[Accueil](../README.fr.md) · [English](install.md) · **Français**

Cet assistant installe **notre APK SmartTube Shorts Slider**, stable par défaut. Il ne configure pas SmartTube officiel. Il utilise uniquement Python 3.10+ et ADB ; le lanceur peut installer les prérequis manquants.

## 1. Préparer la TV

- Connectez le PC et la TV au même réseau local.
- Activez le **débogage ADB** dans les options développeur de la TV.
- Relevez son adresse IP dans ses paramètres réseau.
- Gardez une sauvegarde récente avant une mise à jour.

Sur un appareil utilisant l’association sans fil Android, effectuez d’abord `adb pair IP:PORT`, puis utilisez l’adresse et le port de connexion affichés par la TV. Voir la [documentation ADB](https://developer.android.com/tools/adb).

## 2. Copier-coller une commande

**Linux / macOS — Terminal**

```sh
sh -c 's=$(curl -fsSL https://raw.githubusercontent.com/valoche-68/SmartTube-Shorts-Slider/main/tools/start.sh) && sh -c "$s" sh "$@"' sh
```

**Windows — PowerShell**, pas l’invite `cmd`

```powershell
& ([scriptblock]::Create((Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/valoche-68/SmartTube-Shorts-Slider/main/tools/start.ps1').Content))
```

Pas besoin de cloner le dépôt. Le lanceur réutilise Python et ADB s’ils fonctionnent, puis installe seulement les prérequis manquants. Linux utilise le gestionnaire de paquets disponible ; macOS utilise Homebrew, installé si nécessaire ; Windows utilise WinGet. Une validation ou un mot de passe peut être demandé. Ne lancez pas toute la commande avec `sudo`.

Sous Linux/macOS, `curl` doit être disponible pour lancer la commande. Sous Windows, si WinGet manque, le lanceur indique comment installer App Installer puis s’arrête. Aucun changement de politique d’exécution PowerShell n’est nécessaire.

## 3. Suivre l’assistant

1. S’il n’y a aucun appareil connecté, indiquez l’IP de la TV. Le port par défaut est `5555` ; `IP:PORT` permet de le préciser.
2. Acceptez **Autoriser le débogage USB** sur la TV si la demande apparaît, puis revenez dans le terminal. Si la connexion échoue avant cette étape, vérifiez l’IP et le débogage, puis relancez.
3. S’il y a plusieurs appareils, choisissez la TV. Le script affiche l’appareil ciblé, la version et l’architecture détectée par Android.
4. Il télécharge notre APK depuis les releases de **ce dépôt**, compare sa taille et son SHA-256 aux métadonnées publiées, puis demande confirmation. Tapez **o** pour installer.
5. Attendez **Installation vérifiée. Application non lancée.** Ouvrez ensuite Shorts Slider vous-même quand vous le souhaitez.

La stable est sélectionnée par défaut. Une version identique ne sera pas réinstallée, et une rétrogradation est refusée. Les fichiers temporaires sont retirés ; Python et ADB restent disponibles sur le PC.

## Mise à jour et compte existant

L’installation utilise `adb install -r`, sans désinstallation. Android exige une signature compatible pour remplacer l’application ; une mise à jour acceptée conserve ses données. Le script vérifie ensuite la version et, si disponibles, l’UID et la date de première installation. Il ne se connecte pas à votre compte et ne lit pas vos identifiants.

**Si SmartTube officiel ou une variante incompatible occupe le même canal, le script s’arrête.** Il ne désinstalle rien, ne force pas une signature et ne promet pas de migration automatique du compte. Suivez le [guide de migration](migration.fr.md) avant de changer de signature.

L’installation peut arrêter l’ancienne application pendant son remplacement. Lancez-la à un moment où cela ne gêne pas son utilisation. Le script ne lance pas l’application après l’installation.

## Options facultatives

Ajoutez les options à la fin de la commande copiée :

| Option | Effet |
| --- | --- |
| `--connect 192.168.1.50` | Choisir directement l’IP de votre TV — remplacez cet exemple |
| `--device IDENTIFIANT` | Choisir un appareil déjà connecté à ADB |
| `--channel beta` | Installer notre bêta au lieu de notre stable |
| `--dry-run` | Lire les informations de la TV et de la release, sans télécharger ni installer l’APK |
| `--download-only` | Télécharger et vérifier l’APK sur le PC, sans ADB ; universel par défaut |
| `--download-only --arch armeabi-v7a` | Choisir une architecture pour le téléchargement seul |
| `--yes` | Accepter l’installation sans question ; appareil non ambigu obligatoire |
| `--help` | Afficher l’aide |

Si le projet est déjà téléchargé, utilisez `sh tools/start.sh`, `tools/start.ps1` dans PowerShell, ou directement `python3 tools/install_slider.py` avec Python et ADB déjà disponibles.

## Voir tout le code

[Installateur Python complet](../tools/install_slider.py) · [Lanceur Linux/macOS](../tools/start.sh) · [Lanceur Windows](../tools/start.ps1)

Les tests automatisés utilisent de faux appareils ADB. Le téléchargement réel des APK peut être vérifié indépendamment avec `--download-only` ; cela ne constitue pas un essai d’installation sur chaque modèle de TV.
