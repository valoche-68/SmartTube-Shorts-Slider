# Politique de confidentialité de SmartTube (version F-Droid)

[Accueil](README.fr.md) · [English](PRIVACY.md) · **Français**

Ce document du projet officiel concerne uniquement la version F-Droid. Il ne décrit pas les APK stable ou bêta de Shorts Slider.

**Dernière mise à jour :** 21 mars 2026

Cette politique de confidentialité s’applique spécifiquement à la **variante F-Droid** de SmartTube (identifiant Android : `app.smarttube.fdroid`). Cette version est adaptée à la protection de la vie privée et aux critères d’inclusion de F-Droid.

## 1. Portée de cette politique

Ce document concerne **uniquement la version F-Droid**. D’autres versions ou variantes de l’application, comme Stable et Beta, peuvent proposer des fonctions supplémentaires, notamment la mise à jour automatique ou les rapports de plantage, retirées de cette version F-Droid.

## 2. Collecte et traitement des données

- **Aucun serveur applicatif :** la version F-Droid fonctionne entièrement comme une application cliente. Elle ne communique avec aucun serveur contrôlé par les développeurs.
- **Aucune télémétrie ni analyse d’utilisation :** cette version ne contient aucun code de suivi, de télémétrie ou d’analyse, comme Firebase ou Crashlytics. Nous ne surveillons pas votre utilisation de l’application.
- **Aucun suivi des mises à jour :** le mécanisme de mise à jour intégré est désactivé dans cette variante. Les mises à jour sont gérées exclusivement par le client F-Droid.

## 3. Services tiers (YouTube/Google)

- **Authentification :** la connexion utilise le parcours officiel Google OAuth 2.0. Cette méthode permet d’autoriser l’application sans communiquer votre mot de passe aux développeurs.
- **Stockage local :** les jetons d’authentification sont stockés exclusivement dans le stockage local sécurisé de votre appareil. Ils ne sont jamais transmis aux développeurs ni stockés par eux.
- **Flux de données :** les données vidéo et les informations du compte sont récupérées directement depuis les serveurs YouTube/Google vers votre appareil.

## 4. Services communautaires et API tierces

Pour fournir ses fonctions principales et complémentaires, l’application communique avec les services communautaires suivants :

- **SponsorBlock :** l’application envoie l’identifiant de la vidéo visionnée à l’API SponsorBlock pour récupérer les segments à ignorer proposés par la communauté.
- **DeArrow :** elle envoie l’identifiant de la vidéo à l’API DeArrow pour récupérer les titres proposés par la communauté.
- **Return YouTube Dislike (RYD) :** elle envoie l’identifiant de la vidéo à l’API RYD pour récupérer une estimation des mentions « Je n’aime pas ».
- **Requêtes anonymes de métadonnées :** ces requêtes sont en lecture seule et ne contiennent ni identifiant personnel, ni jeton de compte Google, ni données de profil propres à l’utilisateur.
- **Communications générales avec les API :** l’application peut communiquer avec d’autres infrastructures tierces, notamment les services officiels YouTube/Google, uniquement pour récupérer le contenu multimédia et les métadonnées nécessaires à son fonctionnement. Ces requêtes fonctionnelles n’impliquent aucune collecte ni aucun stockage de données personnelles par les développeurs.

## 5. Décisions automatisées et profilage

Conformément à l’**article 15 du RGPD**, nous confirmons pour cette version :

- **Aucun profilage :** nous ne suivons pas le comportement des utilisateurs pour créer des profils.
- **Aucune décision automatisée :** l’application n’utilise ni algorithmes ni IA pour prendre des décisions concernant les utilisateurs ou manipuler le classement des contenus. Les contenus sont présentés tels qu’ils sont fournis par l’API YouTube.

## 6. Liens externes et dons

L’application contient des liens et adresses statiques vers la documentation du projet sur GitHub et vers des moyens de don, comme PayPal, Patreon, Bitcoin, Ethereum et d’autres cryptomonnaies.

- **Action manuelle uniquement :** ces liens ne se déclenchent pas automatiquement. Aucune donnée n’est transmise tant que l’utilisateur ne clique pas sur un lien ou ne copie pas une adresse.
- **Politiques tierces :** lorsque vous quittez l’application pour une plateforme de don ou utilisez un portefeuille tiers, vos données relèvent des politiques de confidentialité de ces services.

## 7. Vos droits (RGPD / CCPA)

Cette variante ne stocke ni ne transmet de données personnelles aux développeurs. Nous ne détenons donc aucun enregistrement identifiable, comme un nom, un courriel ou une adresse IP, associé à votre identité. Nous n’avons par conséquent aucune donnée à fournir ou supprimer sur demande.

## 8. Contact

Pour toute question technique sur l’architecture de confidentialité de la version F-Droid, ouvrez un ticket sur le dépôt GitHub officiel.
