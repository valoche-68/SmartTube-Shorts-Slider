# SmartTube Shorts Slider — guide complet

[Accueil](../README.fr.md) · [English](user-guide.md) · **Français**

## Notre version de SmartTube

Ce projet fournit un **APK personnalisé**, distinct de SmartTube officiel. Il reprend ses réglages natifs, mais modifie aussi la reconnaissance des Shorts, la conservation de leur identité et la sélection du suivant. Le projet est indépendant, sans affiliation avec le développeur officiel.

**Sur un nouveau profil :** haut/bas, lecture automatique, bouton visible et préparation du suivant sont activés. Une mise à jour conserve les valeurs enregistrées. **Aucun script officiel n’est nécessaire pour notre APK.**

[Utiliser les Shorts et modifier les quatre réglages →](manual-setup.fr.md)

Le bouton avant **Qualité** commande l’automatique : ON enchaîne les Shorts disponibles, OFF répète le Short. Il partage le réglage **Short en boucle**. Son masquage est indépendant de la lecture automatique. L’enchaînement s’arrête si aucun Short suivant n’est disponible ; il ne crée pas de flux infini.

Une longue vidéo verticale n’est pas reconnue comme Short du seul fait de son format. Les commandes du lecteur doivent être masquées pour que les raccourcis de navigation agissent sur les vidéos.

## Préparation du suivant et vitesse

Pendant la lecture, une demande récupère les formats et adresses d’**un seul Short suivant**. Le résultat reste dans un contexte séparé du cache et de l’identifiant d’historique de la vidéo courante. S’il est prêt et encore valide, il peut être utilisé au passage au suivant ; sinon la lecture normale démarre sans attendre sa préparation.

L’officiel prépare lui aussi des informations de formats dans certains cas. Notre modification porte sur le déclenchement pour les Shorts, l’isolation du résultat et l’option pour le désactiver ; nous ne présentons pas toute préparation comme une exclusivité du projet.

**Le gain de vitesse n’a pas été mesuré.** Le premier Short peut encore être long à charger : il n’est pas préparé avant son ouverture. Il n’y a ni second décodeur, ni vidéo entièrement téléchargée à l’avance, ni réserve garantie de dix à vingt Shorts. Les tampons et la pagination officiels sont conservés.

## SmartTube officiel

Les préférences natives existent dans les bases étudiées, mais les essais rapportés sur Fire TV n’ont pas reproduit la navigation et l’automatique attendus. Le tutoriel et le script ne sont donc plus proposés comme solution équivalente à notre APK.

[Comprendre les limites des réglages officiels et le statut expérimental du script →](official-settings.fr.md)

## Télécharger et mettre à jour

**[Dernière stable](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases/latest)** · **[Bêtas et toutes les versions](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases)**

| APK | À choisir selon les architectures prises en charge par Android |
| --- | --- |
| `armeabi-v7a` | ARM 32 bits, fréquent sur les Fire TV |
| `arm64-v8a` | ARM 64 bits |
| `x86` | Android x86 / émulateurs compatibles |
| `universal` | Contient les trois architectures ci-dessus ; plus volumineux |

Le modèle commercial ne suffit pas toujours à choisir : un appareil 64 bits peut exécuter un système 32 bits. ADB peut afficher les architectures autorisées avec `adb shell getprop ro.product.cpu.abilist`.

### Installer et mettre à jour

Les identifiants Android sont `org.smarttube.stable` et `org.smarttube.beta`. Les mises à jour de Shorts Slider utilisent le certificat publié ci-dessous. Une mise à jour de même identifiant et même signature conserve les données : **ne désinstallez pas l’application pour la mettre à jour**. Gardez une sauvegarde récente.

### Vous utilisez l’application officielle

L’identifiant Android est le même, mais la signature est différente : les deux versions du même canal ne peuvent pas cohabiter ou se remplacer directement. Les réglages et le script officiels ne sont pas une alternative validée pour obtenir le comportement de Shorts Slider : voir [leurs limites](official-settings.fr.md).

Si vous choisissez le fork, créez une sauvegarde complète, copiez-la sur votre PC, vérifiez que le ZIP est lisible et conservez les fichiers de comptes avec précaution. Téléchargez et vérifiez le nouvel APK avant toute désinstallation. Une signature de debug différente nécessite également une migration ; le projet ne promet pas une mise à jour directe dans ce cas. Voir le [guide de migration](migration.md).

## Des publications vérifiables

- Deux canaux : chaque stable et chaque bêta provient du **tag officiel correspondant**, avec ses sous-modules épinglés et nos modifications versionnées.
- Recherche de nouvelles releases toutes les six heures. Si les sources changent de façon incompatible, la publication est bloquée ; aucune fusion forcée de `master`.
- Un même échec n’est pas relancé en boucle : il faut une nouvelle source, une nouvelle révision des modifications ou une relance manuelle.
- Contrôle des versions, identifiants, architectures, adresses de mise à jour et signatures des APK avant publication.
- Chaque release contient `build-info.json` et `SHA256SUMS`, ainsi que des liens vers les rapports VirusTotal lorsqu’ils sont disponibles. **Aucun score antivirus n’est inventé.**

### Certificat de signature

Empreinte SHA-256 :

```text
80a1a2db29be237b85486957804c21ddfa1a6c0371b93f2bd293e134aa138838
```

La publication automatique ne garantit pas la compatibilité de toutes les futures modifications officielles. Les essais sur les appareils restent utiles, notamment pour les bêtas.

## Développer et contribuer

Voir [la construction, les tests et l’automatisation](development.md). Les clés privées, mots de passe, exports de conversations et sauvegardes personnelles sont exclus de Git et contrôlés avant commit et en CI. Les sauvegardes peuvent contenir des accès aux comptes : ne les joindre ni aux tickets ni aux rapports publics.

[Licence MIT](../LICENSE). Crédits à [Yurii Liskov et aux contributeurs de SmartTube](https://github.com/yuliskov/SmartTube). Les dépendances conservent leurs licences respectives.
