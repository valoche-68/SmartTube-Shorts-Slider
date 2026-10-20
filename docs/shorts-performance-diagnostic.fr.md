# Diagnostic des transitions entre Shorts

État du 20 octobre 2026 : corrections locales testées, sans publication ni installation sur la Fire TV.

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

La commande Gradle standard n’a pas pu résoudre toutes ses dépendances Android : le dépôt Google ne répondait pas et le cache était incomplet. Cette validation ciblée ne remplace donc pas une construction Android complète ni l’essai sur appareil. Aucun nouvel APK n’a été publié ou installé.

## Prochain essai, quand la TV sera disponible

Installer la version de test seulement à la demande de l’utilisateur. Comparer plusieurs transitions depuis l’accueil, puis une autre section, avec la préparation activée et désactivée. Lire les nouvelles traces pour séparer le temps d’obtention des formats du temps de démarrage du lecteur. Vérifier aussi Bas rapide, retour Haut, sortie du lecteur et réseau défaillant.
