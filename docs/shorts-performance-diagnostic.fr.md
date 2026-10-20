# Diagnostic des transitions entre Shorts

État du 20 octobre 2026 : stable corrigée construite et installée sur la Fire TV à la demande de l’utilisateur, sans lancement de l’application. Les releases publiques restent inchangées.

## Ce que les journaux permettent de dire

Lecture seule du tampon Android existant, sans lancement, navigation, arrêt de SmartTube ni effacement des logs. La capture couvre environ six minutes et contient 639 lignes du processus SmartTube. Les fichiers bruts restent privés hors du dépôt.

Des suggestions ont échoué avec un résultat absent. Un délai réseau a aussi été dépassé pendant la synchronisation de l’historique authentifié ; cette pile ne prouve pas un blocage de la préparation du Short suivant. La version installée ne journalise pas les succès, échecs et durées de cette préparation. Aucun temps de transition précis ne peut être déduit de cette capture.

## Défauts confirmés dans le code

- Les événements de source et de métadonnées peuvent arriver avant que le lecteur soit prêt. La condition « lecture en cours » empêche alors la préparation. La reprise périodique ne se fait qu’une fois par minute.
- Si Bas est pressé pendant une préparation, l’ancienne consommation du cache annule la requête utile puis lance une nouvelle recherche de formats pour la même vidéo.
- Le service isolé ne reprenait pas le choix de client de récupération en cours et pouvait effacer ce choix à l’activation.

## Corrections locales

La préparation est aussi déclenchée à l’événement réel de démarrage de lecture. Une requête déjà en cours pour le Short choisi est transférée à la lecture au premier plan, avec un propriétaire unique pour son annulation. Une erreur, un résultat vide ou devenu invalide entraîne un seul repli vers la lecture normale. Le choix de client de récupération est copié sans partager les caches et un choix plus récent reste prioritaire.

Les traces `ShortsPreparation` enregistrent les étapes et les durées : préparation démarrée/prête, résultat disponible ou manquant, transfert d’une requête en cours, repli normal, formats reçus et lecture prête. Elles ne contiennent ni identifiant vidéo, ni adresse de lecture, ni compte ou jeton.

Les tampons vidéo officiels restent inchangés. Aucun gain chiffré n’est annoncé avant un essai sur appareil.

## Validation locale

Les trois sources Java modifiées compilent sous JDK 17. Les 21 tests ciblés passent : neuf tests du préchargeur, sept tests du cycle du lecteur et cinq tests du choix de client isolé. Ils ont été exécutés avec JUnit et Robolectric 4.11.1, Android SDK simulé 28, en réutilisant les classes déjà compilées des autres modules. Les 60 contrôles Python passent également (neuf cas Windows sont ignorés sur Linux).

Le dépôt Google ne répondait pas depuis le PC et le cache local était incomplet. La [construction complète GitHub](https://github.com/valoche-68/SmartTube-Shorts-Slider/actions/runs/39502417942) a ensuite réussi sur la branche `codex/shorts-preparation-validation` : 54 tests du module commun et 7 tests média, aucun échec. Les quatre APK signés ont été contrôlés (signature, identifiant, version, architectures et adresses de mise à jour). L’archive des sources et les APK sont disponibles dans les artefacts de validation, sans création de release.

La stable ARMv7, de code interne 244603, a remplacé la version installée par `adb install -r`. L’APK relu sur l’appareil correspond au fichier vérifié ; l’UID et la date de première installation sont conservés. Aucune désinstallation, suppression de données ou ouverture de l’application n’a été effectuée. Le gain de vitesse reste à confirmer par l’utilisateur.

## Prochain essai

La version corrigée est installée et attend son premier lancement par l’utilisateur. Comparer plusieurs transitions depuis l’accueil, puis une autre section, avec la préparation activée et désactivée. Lire les nouvelles traces pour séparer le temps d’obtention des formats du temps de démarrage du lecteur. Vérifier aussi Bas rapide, retour Haut, sortie du lecteur et réseau défaillant.
