# SmartTube officiel — limites des réglages et du script

[Accueil](../README.fr.md) · [English](official-settings.md) · **Français**

**La configuration de SmartTube officiel n’est pas une alternative validée à Shorts Slider pour notre usage.** L’activation des options n’a pas reproduit la navigation et l’enchaînement attendus pendant les essais rapportés sur Fire TV. Cela ne démontre pas leur impossibilité sur tous les appareils ou toutes les versions.

## Ce qui a été vérifié dans le code

Les bases officielles **32.56 et 32.68** contiennent des préférences de navigation Shorts, de boucle et de playlist de section. Leur présence ne suffit pas à garantir le résultat dans le lecteur.

Dans la base **32.68**, les raccourcis Shorts du lecteur dépendent notamment de l’appartenance de la vidéo à un **groupe Shorts**. Activer la préférence ne modifie ni cette reconnaissance ni la sélection de la vidéo suivante. Un Short ouvert depuis l’accueil peut donc ne pas suivre le même parcours qu’un Short d’une section dédiée.

Le script ne fait que modifier des valeurs dans une sauvegarde officielle. Il ne corrige pas ce parcours, n’ajoute pas le bouton et ne reproduit pas notre gestion de préparation. Ses tests sur sauvegardes synthétiques vérifient les modifications de valeurs et leur annulation, pas le fonctionnement du lecteur sur TV.

## Ce qui est propre à notre version

Shorts Slider conserve les réglages natifs mais modifie aussi la reconnaissance des Shorts, la conservation de leur identité et le choix du Short suivant. Il ajoute le bouton ON/OFF et une préparation facultative dans un contexte séparé.

La navigation haut/bas et l’automatique sont déjà activées sur un nouveau profil de notre APK. Consultez [son guide de réglages](manual-setup.fr.md) pour les désactiver, masquer le bouton ou désactiver la préparation. **Le script officiel ne s’utilise pas pour configurer notre APK** ; il refuse les versions personnalisées.

## Statut de l’assistant officiel

Le script est conservé comme outil **expérimental de manipulation de sauvegardes**, pas comme méthode recommandée pour obtenir le comportement de Shorts Slider. Son parcours complet de restauration sur TV n’est pas validé. Les formats étudiés sont ceux de 32.56 et 32.68 ; une version inconnue est refusée.

Les commandes et la procédure restent dans la [documentation technique de l’assistant](configuration-native.fr.md), pour des essais volontaires avec sauvegarde. Modifier le mode global de lecture peut aussi faire enchaîner les vidéos longues. Aucune nouvelle restauration sur TV n’est nécessaire pour utiliser Shorts Slider.

Références de la base étudiée : [raccourcis du lecteur](https://github.com/yuliskov/SmartTube/blob/32.68s/common/src/main/java/com/liskovsoft/smartyoutubetv2/common/app/models/playback/controllers/PlayerUIController.java), [choix du suivant](https://github.com/yuliskov/SmartTube/blob/32.68s/common/src/main/java/com/liskovsoft/smartyoutubetv2/common/app/models/playback/controllers/SuggestionsController.java), [préférences](https://github.com/yuliskov/SmartTube/blob/32.68s/common/src/main/java/com/liskovsoft/smartyoutubetv2/common/prefs/PlayerTweaksData.java).
