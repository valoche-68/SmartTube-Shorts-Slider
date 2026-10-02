# SmartTube Shorts Slider

**Les Shorts sur TV, avec les réglages qui vous conviennent.**

**Français** · [English](README.en.md) · [Versions APK](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases) · [Projet officiel](https://github.com/yuliskov/SmartTube)

[![Validation](https://github.com/valoche-68/SmartTube-Shorts-Slider/actions/workflows/CI.yml/badge.svg)](https://github.com/valoche-68/SmartTube-Shorts-Slider/actions/workflows/CI.yml)
[![Licence MIT](https://img.shields.io/badge/licence-MIT-blue.svg)](LICENSE)

Deux possibilités : **garder SmartTube officiel et configurer ses fonctions natives**, ou **installer cette version personnalisée pour son bouton de lecture automatique et la préparation du Short suivant**.

## 1. Garder SmartTube officiel

La navigation entre Shorts et leur enchaînement existent déjà dans l’application officielle. Aucun APK personnalisé n’est nécessaire pour les activer.

| Besoin | Réglage officiel |
| --- | --- |
| Short suivant/précédent avec haut/bas | Paramètres → Général → Réaffectation des touches → Naviguer entre les Shorts avec les boutons haut/bas |
| Préférer gauche/droite, ou désactiver les raccourcis | Même menu ; choisir la navigation souhaitée |
| Enchaîner à la fin d’un Short | Paramètres → Lecteur vidéo → Divers → désactiver « Short en boucle », et choisir le mode de lecture « vidéo suivante » |
| Suivre les vidéos de la section ouverte | Lecteur vidéo → Divers → Utiliser le contenu de la section actuelle comme playlist |

L’enchaînement dépend des vidéos disponibles et de leur identification comme Shorts. Le mode de lecture global concerne aussi les vidéos longues.

### Un assistant depuis le PC

Le [script guidé](docs/configuration-native.md) accompagne une modification réversible des réglages à partir d’une **sauvegarde officielle récente**. Il fonctionne avec Python 3.10+ et ADB sous Linux, macOS et Windows. Il n’utilise pas le root et n’installe pas d’application.

```sh
# Depuis le dossier du projet, après connexion ADB à la TV
python3 tools/configure_shorts.py
# Windows : tools\configure_shorts.cmd
```

Il propose haut/bas, gauche/droite ou aucun raccourci ; lecture automatique ou boucle ; playlist de la section ; consultation et annulation des changements. L’import doit être validé sur la TV.

**Compatibilité vérifiée dans le code : SmartTube officiel 32.56 stable et bêta.** Les versions inconnues sont refusées plutôt que modifiées à l’aveugle. Le test de bout en bout sur Fire TV reste à effectuer ; les réglages manuels ci-dessus restent disponibles.

> Le script n’ajoute **ni bouton dans le lecteur, ni préparation anticipée**. Il conserve votre APK officiel et ses mises à jour.

## 2. Installer SmartTube Shorts Slider

Cette version reprend le code de SmartTube avec un ensemble limité de modifications. C’est un projet indépendant, maintenu à partir de l’officiel, sans affiliation avec son développeur.

| Fonction | SmartTube officiel | Shorts Slider |
| --- | --- | --- |
| Navigation haut/bas ou gauche/droite | Réglage natif | Même réglage ; haut/bas activé sur un nouveau profil |
| Lecture automatique des Shorts | Réglages natifs | Activée sur un nouveau profil, avec bouton ON/OFF |
| Bouton avant « Qualité » | Absent | Présent uniquement sur les Shorts, masquable |
| Préparation des informations du Short suivant | Pas notre préparation anticipée | Activée par défaut, désactivable |
| Tampons vidéo et pagination | Comportement officiel | Comportement officiel conservé |

### Le bouton, simplement

- **ON :** enchaîner les Shorts disponibles.
- **OFF :** répéter le Short en cours.
- Le bouton et « Short en boucle » partagent le même réglage.
- Pour masquer le bouton : **Lecteur vidéo → Boutons du lecteur → Afficher le bouton de lecture automatique des Shorts**. Le masquer ne change pas la lecture automatique.
- Pour désactiver la préparation : **Lecteur vidéo → Divers → Préparer le Short suivant**.

Les choix existants sont conservés lors d’une mise à jour. Les réglages du fork s’appliquent aux Shorts identifiés ; une vidéo longue verticale n’est pas automatiquement un Short. L’enchaînement des Shorts s’arrête lorsqu’aucun Short suivant n’est disponible.

### Ce que prépare l’application

Pendant la lecture, une demande récupère les formats et adresses de lecture d’**un seul Short suivant**. Son résultat reste séparé du cache et de l’identifiant d’historique de la vidéo courante, puis peut être utilisé au passage au suivant. En cas d’échec ou d’expiration, le chargement normal reste disponible.

Cela peut éviter une partie du travail au changement de vidéo. **Le gain de vitesse n’a pas encore été mesuré sur la Fire TV du mainteneur.** Il dépend du réseau, de la TV et de YouTube. Il n’y a ni second décodeur, ni vidéo entièrement téléchargée à l’avance, ni réserve garantie de 10 à 20 Shorts.

## Télécharger et mettre à jour

**[Dernière stable](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases/latest)** · **[Bêtas et toutes les versions](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases)**

| APK | À choisir selon les architectures prises en charge par Android |
| --- | --- |
| `armeabi-v7a` | ARM 32 bits, fréquent sur les Fire TV |
| `arm64-v8a` | ARM 64 bits |
| `x86` | Android x86 / émulateurs compatibles |
| `universal` | Contient les trois architectures ci-dessus ; plus volumineux |

Le modèle commercial ne suffit pas toujours à choisir : un appareil 64 bits peut exécuter un système 32 bits. ADB peut afficher les architectures autorisées avec `adb shell getprop ro.product.cpu.abilist`.

### Vous utilisez déjà l’ancien fork

Les nouveaux APK gardent les identifiants `org.smarttube.stable` / `org.smarttube.beta` et la même signature personnelle. Une mise à jour compatible conserve les données : **ne désinstallez pas l’application**. Faites néanmoins une sauvegarde récente avant migration.

L’ancienne stable disposait d’une adresse de mise à jour cassée : le fichier de compatibilité `smarttube_stable2.json` est fourni avec les nouvelles stables. L’ancienne bêta pointait vers l’officiel : installer manuellement une première fois la nouvelle bêta du fork.

### Vous utilisez l’application officielle

L’identifiant Android est le même, mais la signature est différente : les deux versions du même canal ne peuvent pas cohabiter ou se remplacer directement. **Essayez d’abord les réglages natifs ou le script.**

Si vous choisissez le fork, créez une sauvegarde complète, copiez-la sur votre PC, vérifiez que le ZIP est lisible et conservez les fichiers de comptes avec précaution. Téléchargez et vérifiez le nouvel APK avant toute désinstallation. Une signature de debug différente nécessite également une migration ; le projet ne promet pas une mise à jour directe dans ce cas. Voir le [guide de migration](docs/migration.md).

## Des publications vérifiables

- Deux canaux : chaque stable et chaque bêta provient du **tag officiel correspondant**, avec ses sous-modules épinglés et nos modifications versionnées.
- Recherche de nouvelles releases toutes les six heures. Si les sources changent de façon incompatible, la publication est bloquée ; aucune fusion forcée de `master`.
- Un même échec n’est pas relancé en boucle : il faut une nouvelle source, une nouvelle révision des modifications ou une relance manuelle.
- Contrôle des versions, identifiants, architectures, adresses de mise à jour et signatures des APK avant publication.
- Chaque release contient `build-info.json` et `SHA256SUMS`, ainsi que des liens vers les rapports VirusTotal lorsqu’ils sont disponibles. **Aucun score antivirus n’est inventé.**

Empreinte SHA-256 du certificat de ce fork :

```text
80a1a2db29be237b85486957804c21ddfa1a6c0371b93f2bd293e134aa138838
```

La publication automatique ne garantit pas la compatibilité de toutes les futures modifications officielles. Les essais sur les appareils restent utiles, notamment pour les bêtas.

## Développer et contribuer

Voir [la construction, les tests et l’automatisation](docs/development.md). Les clés privées, mots de passe, exports de conversations et sauvegardes personnelles sont exclus de Git et contrôlés avant commit et en CI. Les sauvegardes peuvent contenir des accès aux comptes : ne les joindre ni aux tickets ni aux rapports publics.

[Licence MIT](LICENSE). Crédits à [Yurii Liskov et aux contributeurs de SmartTube](https://github.com/yuliskov/SmartTube). Les dépendances conservent leurs licences respectives.
