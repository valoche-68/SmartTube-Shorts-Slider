# Diagnostic des transitions entre Shorts

État du 21 octobre 2026 : les essais de la révision interne 3 ont révélé des régressions malgré ses tests automatisés. Le correctif suivant est en validation ; aucune amélioration de vitesse n'est encore confirmée sur appareil.

## Journaux et causes identifiées

Les journaux Android ont été lus sans lancer, arrêter ou manipuler SmartTube. La dernière capture couvre environ trois minutes et contient 554 lignes du processus. Elle indique un cache manquant, puis aucune recherche de formats au premier plan, réception de formats ou préparation démarrée. Cette absence correspond au blocage constaté dans le code ; elle ne mesure pas un délai réseau de vingt secondes. Les fichiers bruts restent privés, hors du dépôt.

Deux défauts du contrôleur expliquent les symptômes :

- Le présentateur affecte la nouvelle vidéo **après** avoir notifié les contrôleurs. Une vérification de l'identité courante exécutée pendant cette notification abandonnait donc la demande avant son envoi. Les anciens tests avaient déjà affecté la nouvelle vidéo et masquaient ce défaut.
- L'enveloppe d'abonnement restait marquée active après la fin de la recherche de formats. Le contrôle de fin de lecture bloquait alors le passage automatique au suivant. La navigation manuelle utilisait un autre parcours.

Deux attentes supplémentaires ont été retirées : une préparation inachevée n'est plus transférée au premier plan, et un Short déjà connu n'attend plus la pagination de la section avant d'être proposé.

## Parcours restauré

Le chargement utilise le parcours officiel complet, avec authentification et repli Innertube. La préparation l'exécute dans un service et un cache privés. Seul un résultat terminé et encore valide peut être activé ; sinon la lecture normale démarre immédiatement. Aucun historique n'est écrit par cette préparation.

Les résultats sont livrés sur le fil principal après la notification du présentateur. Une génération de requête annule les anciens résultats lors des changements rapides. Le contrôleur conserve l'abonnement réel, dont la fin est visible par le passage automatique. Bouton OFF remet le Short en boucle.

La préparation reste limitée aux formats et adresses d'une seule vidéo suivante, avec annulation, contrôle de validité et délai avant nouvelle tentative après erreur. Les tampons vidéo officiels restent inchangés.

Les traces `ShortsPreparation` distinguent cache prêt, cache manquant ou encore en préparation, recherche normale, formats reçus et lecture prête. Elles ne contiennent ni identifiant vidéo, ni adresse de lecture, ni compte ou jeton.

## Validation

Les tests reproduisent maintenant le véritable ordre de `PlaybackPresenter.onNewVideo`, sans préaffecter sa vidéo courante. Ils vérifient le chargement, le passage automatique après fin des formats, la boucle avec le bouton OFF, l'activation différée d'un cache prêt et les changements rapides. Les tests de service vérifient aussi authentification, repli Innertube et isolation du cache.

Les 61 tests du module commun passent localement. Les deux défauts ont aussi été réintroduits séparément dans des copies temporaires du contrôleur : chacun fait échouer trois tests du cycle réel. Les correctifs s’appliquent sans conflit aux sources officielles exactes.

Les sources et les tests sont compilés localement sous JDK 17, puis exécutés avec JUnit et Robolectric 4.11.1, SDK simulé 28, en réutilisant les classes déjà compilées des autres modules. Une construction complète et signée en CI est nécessaire avant livraison. Aucun résultat de test automatisé ne constitue une mesure de fluidité sur Fire TV.

## Prochain essai sur appareil

Depuis l'accueil puis une autre section : vérifier plusieurs transitions, la lecture automatique ON/OFF, Bas rapide et retour Haut. Comparer préparation activée et désactivée en lisant les durées des traces. Le premier Short nécessite toujours son chargement normal. Ne décrire un gain de vitesse qu'après cet essai.
