# Shorts Slider — utilisation et réglages

[Accueil](../README.fr.md) · [English](manual-setup.md) · **Français**

**Ce guide concerne notre APK SmartTube Shorts Slider.** Il ne promet pas le même résultat dans SmartTube officiel. Les essais rapportés avec l’officiel n’ont pas reproduit le comportement attendu ; voir [les limites des réglages officiels](official-settings.fr.md).

## Déjà activé par défaut

Sur un **nouveau profil**, Shorts Slider active la navigation **haut/bas**, la **lecture automatique**, son **bouton dans le lecteur** et la **préparation du Short suivant**. Il n’y a aucun script à exécuter pour les activer dans notre APK.

Sur une installation ou un profil existant, vos choix enregistrés sont conservés. Les valeurs peuvent donc différer de ces valeurs par défaut.

## Passer au suivant ou revenir en arrière

Ouvrez un Short reconnu par l’application et attendez que les commandes du lecteur disparaissent : **↓ Bas** demande le suivant, **↑ Haut** le précédent lorsqu’il est disponible. Avec un menu ou les commandes à l’écran, les flèches servent à naviguer dans cette interface.

Pour changer les raccourcis : **Paramètres → Général → Réaffectation des touches**.

| Votre choix | Option |
| --- | --- |
| Haut/bas | **Naviguer entre les Shorts avec les boutons haut/bas** — activée sur un nouveau profil |
| Gauche/droite | **Sauter les Shorts avec les boutons gauche/droite** — droite = suivant, gauche = précédent |
| Aucun de ces raccourcis Shorts | Décochez l’option de navigation Shorts actuellement activée |

Haut/bas et gauche/droite sont exclusifs : activer l’un désactive l’autre. Changer ces options peut aussi réinitialiser des affectations personnalisées des mêmes touches, notamment le volume pour gauche/droite. Notez vos choix avant de les modifier.

Désactiver les raccourcis ne désactive pas la lecture automatique.

## Lecture automatique ou boucle

Le bouton **Défilement auto des Shorts**, avant **Qualité**, apparaît uniquement pour les Shorts si son affichage est activé :

- **ON :** passer au Short suivant disponible à la fin.
- **OFF :** répéter le Short en cours.

Le bouton partage la préférence **Paramètres → Lecteur vidéo → Divers → Short en boucle** : une boucle cochée correspond à l’automatique OFF. Il n’est pas nécessaire de changer le mode global de lecture pour piloter les Shorts dans notre version.

L’enchaînement s’arrête si aucun Short suivant n’est disponible. Le bouton ne crée pas un flux infini.

## Masquer le bouton

Ouvrez **Paramètres → Lecteur vidéo → Gestion des boutons du lecteur** et décochez **Afficher le bouton de lecture automatique des Shorts**.

**Masquer le bouton ne désactive pas l’automatique.** Pour le désactiver, utilisez OFF avant de masquer le bouton, ou cochez **Short en boucle** dans **Divers**.

## Désactiver la préparation du suivant

Dans **Paramètres → Lecteur vidéo → Divers**, décochez **Préparer le Short suivant**. Cette option est activée par défaut ; la navigation et le bouton restent utilisables lorsqu’elle est désactivée.

La préparation récupère les formats et adresses de lecture d’**un seul Short suivant**. Elle ne télécharge pas dix vidéos et ne prépare pas le premier Short avant son ouverture. Le premier chargement peut donc rester long ; aucun gain de vitesse n’est encore mesuré.

## Profils et liste de lecture

Avec des paramètres distincts par compte, vérifiez les options dans le profil concerné. Sinon, les réglages sont partagés.

**Utiliser le contenu de la section actuelle comme playlist**, dans **Lecteur vidéo → Divers**, reste un réglage natif facultatif qui concerne aussi les autres vidéos. Notre navigation Shorts n’exige pas de l’activer pour accéder aux Shorts disponibles depuis l’accueil.

Une longue vidéo verticale n’est pas considérée comme un Short du seul fait de son format. Pour l’installation, la conservation du compte et les mises à jour, voir le [guide complet](user-guide.fr.md).
