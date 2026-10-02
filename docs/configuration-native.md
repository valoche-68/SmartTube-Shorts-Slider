# Configurer SmartTube officiel depuis un PC

[Accueil en français](../README.fr.md) · [English overview](../README.md)

Le script configure les fonctions natives. Il n'ajoute ni bouton ni préparation anticipée, n'installe aucun APK, ne désinstalle rien et n'utilise pas le root. Sa logique de modification et d'annulation est testée sur des sauvegardes synthétiques. Le parcours complet sur Fire TV reste à valider.

## Préparer l'ordinateur et la TV

Installer [Python 3.10 ou supérieur](https://www.python.org/downloads/) et les [Android SDK Platform Tools](https://developer.android.com/tools/releases/platform-tools). Ajouter `adb` au PATH.

Activer le débogage ADB dans les options développeur de la TV, connecter l'ordinateur et accepter la demande sur la TV. Selon l'appareil, utiliser `adb connect ADRESSE:PORT` ou l'association `adb pair`. Ne pas exposer ADB sur Internet. La [documentation Android](https://developer.android.com/tools/adb) décrit ces modes.

## Lancer sans télécharger de fichier à la main

Après la préparation ci-dessus, copiez-collez **une seule commande** dans votre console :

**Linux / macOS — Terminal**

```sh
sh -c 's=$(curl -fsSL https://raw.githubusercontent.com/valoche-68/SmartTube-Shorts-Slider/main/tools/start.sh) && sh -c "$s" sh "$@"' sh
```

**Windows — PowerShell**

```powershell
& ([scriptblock]::Create((Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/valoche-68/SmartTube-Shorts-Slider/main/tools/start.ps1').Content))
```

La commande récupère le lanceur de ce dépôt, puis celui-ci télécharge uniquement `configure_shorts.py` dans un dossier temporaire. Le menu garde l’accès au clavier. Si le téléchargement échoue, aucun fichier incomplet n’est exécuté. Le fichier temporaire est supprimé à la fermeture, sans supprimer les sauvegardes privées. Git n’est pas nécessaire ; les lanceurs n’installent pas Python ou ADB et ne modifient pas les règles d’exécution de PowerShell.

Pour obtenir l’aide ou utiliser la bêta, on peut ajouter `--help` ou `--channel beta` à la fin de la commande. Les autres options du script fonctionnent de la même manière.

Si le projet est déjà présent sur le PC, les commandes locales restent disponibles :

```sh
python3 tools/configure_shorts.py
# Linux / macOS : tools/configure_shorts.sh
# Windows : tools\configure_shorts.cmd
```

## Parcours guidé

1. Le script contrôle la version installée. Les versions vérifiées sont **32.56 stable et bêta, code Android 2446**. Il refuse une version inconnue ; utiliser les réglages manuels de l'accueil dans ce cas.
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
