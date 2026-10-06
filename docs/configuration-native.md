# Configurer SmartTube officiel depuis un PC

[Accueil en français](../README.fr.md) · [English overview](../README.md)

Le script configure les fonctions natives. Il n'ajoute ni bouton ni préparation anticipée, n'installe aucun APK, ne désinstalle rien et ne nécessite pas le root sur la TV. Sa logique de modification et d'annulation est testée sur des sauvegardes synthétiques. Le parcours complet sur Fire TV reste à valider.

[Faire ces réglages manuellement, à la télécommande →](manual-setup.fr.md)

## Installation automatique des prérequis

La commande ci-dessous vérifie **Python 3.10+** et **ADB**, conserve les outils déjà utilisables et installe uniquement les prérequis manquants :

| Système | Installation utilisée |
| --- | --- |
| Linux | `apt-get`, `dnf`, `pacman`, `zypper` ou `apk`, avec les paquets des dépôts configurés |
| macOS | [Homebrew](https://docs.brew.sh/Installation), installé depuis sa source officielle s’il manque ; Python et [Android Platform Tools](https://formulae.brew.sh/cask/android-platform-tools) |
| Windows | [WinGet](https://learn.microsoft.com/en-us/windows/package-manager/winget/install), avec `Python.Python.3.13` et `Google.PlatformTools`, pour l’utilisateur courant |

Le système peut demander une confirmation ou un mot de passe administrateur. Sur Linux, seuls les appels au gestionnaire de paquets utilisent `sudo` si nécessaire. Homebrew peut aussi demander l’installation des outils de développement Apple. **Ne lancez pas toute la commande avec `sudo`.**

Sous Linux/macOS, la commande nécessite `curl`. Sous Windows, si WinGet manque, le lanceur indique comment installer [App Installer de Microsoft](https://apps.microsoft.com/detail/9nblggh4nns1), puis s’arrête. Un gestionnaire non pris en charge, des paquets indisponibles ou une version de Python trop ancienne après installation provoquent aussi un arrêt. Il reste possible d’installer [Python](https://www.python.org/downloads/) et [ADB](https://developer.android.com/tools/releases/platform-tools) manuellement, puis de relancer.

Les prérequis sont revérifiés après installation. L’aide (`--help`) et le travail sur une sauvegarde locale (`--backup`) nécessitent Python, mais n’installent pas ADB. Les outils installés restent sur le PC pour les prochains lancements.

## Lancer sans télécharger de fichier à la main

Copiez-collez **une seule commande** dans votre console :

**Linux / macOS — Terminal**

```sh
sh -c 's=$(curl -fsSL https://raw.githubusercontent.com/valoche-68/SmartTube-Shorts-Slider/main/tools/start.sh) && sh -c "$s" sh "$@"' sh
```

**Windows — PowerShell**

```powershell
& ([scriptblock]::Create((Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/valoche-68/SmartTube-Shorts-Slider/main/tools/start.ps1').Content))
```

La commande récupère le lanceur de ce dépôt. Après vérification et installation éventuelle des prérequis, celui-ci télécharge `configure_shorts.py` dans un dossier temporaire. Le menu garde l’accès au clavier. Si le téléchargement échoue, aucun fichier incomplet n’est exécuté. Le dossier temporaire est supprimé à la fermeture, sans supprimer les sauvegardes privées. Git n’est pas nécessaire ; les règles d’exécution de PowerShell restent inchangées.

Pour obtenir l’aide ou utiliser la bêta, on peut ajouter `--help` ou `--channel beta` à la fin de la commande. Les autres options du script fonctionnent de la même manière.

Si le projet est déjà présent sur le PC, `sh tools/start.sh` ou `& ([scriptblock]::Create((Get-Content -Raw .\tools\start.ps1)))` proposent la même installation automatique. Pour lancer uniquement le script local, avec les prérequis déjà installés :

```sh
python3 tools/configure_shorts.py
# Linux / macOS : tools/configure_shorts.sh
# Windows : tools\configure_shorts.cmd
```

## Connecter la TV

Activer le débogage ADB dans les options développeur de la TV, connecter l’ordinateur et accepter la demande sur la TV. Selon l’appareil, utiliser `adb connect ADRESSE:PORT` ou l’association `adb pair`. La [documentation Android](https://developer.android.com/tools/adb) décrit ces modes. Ne pas exposer ADB sur Internet.

Si ADB vient d’être installé, ouvrir un nouveau terminal avant d’utiliser `adb connect`. Avec Homebrew, suivre si nécessaire ses instructions pour ajouter ses outils au `PATH`. Si l’assistant ne trouve aucun appareil connecté, connecter la TV puis relancer la commande ; les prérequis déjà présents ne seront pas réinstallés.

## Parcours guidé

1. Le script contrôle la version installée. Les versions vérifiées sont **32.56 stable et bêta, code Android 2446**. Il refuse une version inconnue ; suivre le [tutoriel manuel](manual-setup.fr.md) dans ce cas, en tenant compte des éventuelles différences de menus.
2. Créer une **nouvelle sauvegarde complète** avec Paramètres → Sauvegarde/restauration → Sauvegarde locale. Indiquer au script le chemin complet du ZIP affiché sur la TV. Les emplacements varient selon Android ; aucune ancienne sauvegarde n'est choisie silencieusement.
3. Choisir navigation, lecture automatique et playlist de section, ou consulter les réglages. Le profil actif est utilisé ; `--profile NOM` permet de choisir un profil déjà présent.
4. Lire le récapitulatif. Activer l'automatique désactive la boucle Shorts et peut sélectionner le mode global « vidéo suivante », qui s'applique également aux vidéos longues.
5. Le script garde `original.zip`, crée `configured.zip` et écrit `undo.json` dans un nouveau dossier privé du PC.
6. Il propose de transférer le ZIP et d'ouvrir l'import officiel. **Valider la restauration sur la TV**, puis relancer l'application. L'arrêt de SmartTube après restauration est normal. Vérifier les réglages.
7. Revenir au terminal après la restauration pour retirer le ZIP temporaire de la TV. Le dossier privé du PC reste disponible pour revenir en arrière.

Ne pas changer d'autres réglages entre la sauvegarde et la restauration : l'import officiel restaure une sauvegarde complète, même si le script n'en a modifié que quelques valeurs.

## Travail sur un ZIP déjà copié

```sh
# Voir l'état, sans modifier la TV
python3 tools/configure_shorts.py --backup sauvegarde.zip --version 32.56 --status

# Simulation : aucun fichier créé, aucun transfert, aucune restauration
python3 tools/configure_shorts.py --backup sauvegarde.zip --version 32.56 \
  --navigation up-down --autoplay on --section on --dry-run

# Préparer le ZIP à importer manuellement
python3 tools/configure_shorts.py --backup sauvegarde.zip --version 32.56 \
  --navigation up-down --autoplay on --section on --output ./backup_shorts_prive
```

`--navigation left-right` choisit gauche/droite ; `off` désactive ces raccourcis. `--autoplay off` remet les Shorts en boucle. Les options omises en mode non interactif laissent leurs réglages en place.

Le ZIP configuré peut être importé avec le gestionnaire de fichiers de la TV ou transféré dans le dossier média de SmartTube, puis ouvert par son import officiel. Si Android refuse le transfert ou l'import, aucune réussite n'est annoncée : utiliser le parcours manuel de sauvegarde/restauration.

## Annuler les changements

Créer d'abord une **nouvelle sauvegarde** de l'état actuel, puis :

```sh
python3 tools/configure_shorts.py --backup sauvegarde_actuelle.zip --version 32.56 \
  --undo /chemin/prive/undo.json
```

Le script rétablit les anciennes valeurs ciblées et conserve les autres réglages de la nouvelle sauvegarde. Si une valeur ciblée a depuis été changée autrement, il s'arrête plutôt que de l'écraser. `original.zip` reste une sauvegarde de secours complète de l'état initial.

## Données privées et limites

Les sauvegardes peuvent contenir des accès aux comptes. Le script ne les envoie à aucun service externe et ne les affiche pas. Les sorties sont créées dans le répertoire utilisateur, avec des permissions restreintes lorsque le système les prend en charge. Sous Windows, conserver ces fichiers dans votre dossier utilisateur protégé ; les modes Unix ne remplacent pas les autorisations Windows.

Ne joindre ni sauvegarde ni journal d'annulation à un ticket GitHub. Les archives ambiguës, chemins dangereux, préférences inconnues et sauvegardes d'applications personnalisées sont refusés. La prise en charge d'une future version nécessite la vérification de son schéma officiel.
