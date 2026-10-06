# Construction et maintenance

## Organisation

`main` contient le développement du fork, la documentation, le script natif et l'automatisation. Les APK publiés sont construits dans un checkout séparé du tag officiel exact : le nom du canal n'est jamais utilisé pour qualifier arbitrairement du code de `master`.

- `fork/config.json` : origine, base de comparaison, révision du fork et empreinte publique attendue du certificat.
- `fork/shorts.patch` : modifications de l'application et tests.
- `fork/mediaservice.patch` : contexte et résultat de préparation séparés de la lecture courante.
- `fork/build.json` dans chaque tag publié : provenance du build. `build-info.json` dans la release ajoute le commit de source final et les empreintes des APK.

Le sous-module média du tag reste épinglé au commit officiel. Son patch public doit être appliqué avant compilation :

```sh
git submodule update --init --recursive
python3 fork/apply_media_patch.py
```

Le fichier de patch est inclus dans chaque tag publié ; il n'y a pas de dépendance à un commit privé de sous-module.

## Développer

Installer JDK 17 et Android SDK 34, build-tools 30.0.3 et NDK 21.0.6113669. Configurer `local.properties` ou `ANDROID_HOME`. Ne jamais versionner `keystore.properties`, une clé ou un mot de passe. Le hook local peut être activé avec :

```sh
git config core.hooksPath .githooks
python3 .github/scripts/check_sensitive_files.py
python3 -m unittest discover -s tools/tests -v
bash gradlew :common:testStstableDebugUnitTest \
  --tests '*ShortsPreferencesTest' --tests '*NextVideoPreloaderTest' --tests '*PlaybackNonceIsolationTest' \
  --tests '*VideoShortsClassificationTest' --tests '*ShortsNavigationTest' \
  :youtubeapi:testStstableDebugUnitTest --tests '*ShortsIdentityTest'
```

Robolectric est fixé à 4.11.1 dans le module commun pour ces tests sous JDK 17 ; l'ancienne version 4.6.1 ne sait pas instrumenter les classes Java 17.

Après une modification de l'application ou du sous-module, **incrémenter la révision de publication**, exécuter `python3 fork/update_patches.py`, puis relire les deux patchs. La génération utilise une liste explicite de fichiers publics pour le patch de l'application. Ne pas ajouter une modification générique au moteur vidéo sans validation spécifique.

Les comportements couverts incluent : migration des préférences, préférences natives cohérentes, masquage indépendant, demandes anticipées dédupliquées et annulables, cache consommable une fois, expiration et contexte d'historique isolé. Les tests de navigation vérifient aussi la conservation de l'identité des Shorts, les listes mixtes sans playlist de section, les fins de liste et l'annulation des réponses tardives. La préparation réutilise le fournisseur de formats dans une instance distincte ; si elle échoue, la lecture normale garde ses propres replis.

## Reproduire une release depuis le dépôt principal

```sh
python3 .github/scripts/release.py prepare --channel stable --tag 32.56s --folder /chemin/neuf/build-stable
python3 .github/scripts/release.py build --channel stable --folder /chemin/neuf/build-stable
```

La préparation exige la configuration locale de signature ignorée par Git, ou les variables `SIGNING_KEY` (base64), `KEY_STORE_PASSWORD`, `ALIAS`, `KEY_PASSWORD`. La clé doit correspondre à l'empreinte publique configurée. Les APK sont contrôlés après construction : package, version interne, signature, bibliothèques natives et adresses de mise à jour compilées.

Une version officielle de code `N`, révision `R` du fork, produit `N * 100 + R`, avec `1 ≤ R < 100`. Exemple : 2446 et révision 1 donnent 244601. Les tags sont `v32.56-stable-slider.1` et `v32.56-beta-slider.1`. Ne jamais remplacer les binaires d'un tag déjà publié ; incrémenter la révision.

## Automatisation GitHub

Le workflow `release-shorts-slider.yml` s'exécute toutes les six heures ou manuellement. Il consulte les releases officielles, ignore annonces et alias, choisit chaque tag exact, initialise les sous-modules, applique les patchs, lance les tests et construit les APK. Les secrets de signature n'apparaissent ni dans les commandes interpolées ni dans les fichiers publiés.

La publication passe par un brouillon dont les fichiers sont téléchargés et comparés avant exposition. Le tag référence le commit de source compilé. Les métadonnées OTA ne changent qu'après publication vérifiée. Le manifeste stable est aussi disponible sous l'alias `smarttube_stable2.json`.

La branche `automation-state` conserve les résultats par canal, commit officiel et empreinte des modifications. Un échec identique est ignoré lors des passages suivants. Pour réessayer : lancement manuel avec `retry=true`. Une réponse d'upload perdue est réconciliée en vérifiant les fichiers présents par leurs noms et leurs octets, puis les fichiers manquants sont envoyés. L'ensemble complet reste obligatoire avant publication.

Après interruption, conserver le brouillon, son tag et le dossier de construction `release-build/<canal>`. La relance peut reprendre ce dossier après contrôle des sources, signatures et architectures. Sans construction locale validée conservée, elle s'arrête pour inspection ; aucun brouillon ni tag n'est supprimé automatiquement. Un APK publié n'est pas remplacé. Un défaut de publication des métadonnées peut être réparé par une relance qui vérifie les sources de la release existante. Une écriture d'état à réponse incertaine est vérifiée par relecture, avec trois tentatives au maximum ; un état concurrent différent est préservé.

Les rapports de tests sont conservés 30 jours dans les artefacts Actions. Aucun workflow ne supprime immédiatement tous les journaux. VirusTotal est indépendant de la preuve de construction : l'action soumet les APK si une clé est configurée, puis ajoute uniquement des liens vers les rapports réels.

## Mise à jour du script natif

Avant d'accepter une nouvelle version officielle, comparer ses préférences `PlayerTweaksData`, `PlayerData`, `GeneralData`, `AppPrefs` et `SharedPreferencesBase` à celles déjà prises en charge. Valider l'encodage, les indices, les valeurs par défaut et la restauration, puis ajouter la version au tableau de compatibilité du script et à sa documentation. L'automatisation des APK ne doit pas élargir silencieusement la compatibilité du script.

## Validation sur appareil

Les tests logiciels et l'inspection des APK ne remplacent pas un essai Fire TV, qui reste à réaliser. Vérifier sur l'appareil une mise à jour sans désinstallation, les préférences conservées, le bouton masqué/affiché, les vidéos longues verticales, les fins de listes, ainsi que le parcours sauvegarde/modification/restauration du script.

Comparer les transitions avec et sans préparation sur le même appareil et le même réseau ; rapporter le protocole et les mesures avant toute affirmation chiffrée. Ne pas publier de logs contenant des adresses de flux signées, des comptes ou des jetons.
