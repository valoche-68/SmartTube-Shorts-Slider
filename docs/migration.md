# Mettre à jour ou changer de signature

## Ancien fork signé avec la clé personnelle

Télécharger la nouvelle stable ou bêta correspondant au canal installé. Vérifier `SHA256SUMS` et l'empreinte du certificat publiée dans le README. Conserver une sauvegarde récente hors de la TV.

Une mise à jour de même identifiant et même signature s'installe sans désinstallation :

```sh
adb install -r /chemin/vers/APK.apk
```

Si Android signale une signature incompatible ou un numéro de version trop bas, arrêter et identifier la version installée. Ne pas ajouter automatiquement une désinstallation ou un contournement de rétrogradation.

L'ancienne bêta doit recevoir une première mise à jour manuelle. Pour l'ancienne stable, le nouvel alias `smarttube_stable2.json` permet au mécanisme existant de trouver le nouvel APK.

## Application officielle ou version de debug

Une signature différente empêche l'installation directe. Le fork garde les identifiants officiels : il ne peut pas cohabiter avec l'officiel du même canal.

1. Tester d'abord les réglages officiels ou le script guidé : cela peut éviter la migration.
2. Si vous choisissez le fork, créer une sauvegarde complète récente dans l'application actuellement installée.
3. Copier le ZIP sur le PC, hors du stockage lié à l'application, vérifier sa lisibilité et conserver une copie. Ne pas supposer qu'une sauvegarde sur la TV survivra à la désinstallation.
4. Télécharger l'APK cible, vérifier son architecture, son SHA-256 et sa signature **avant** de retirer l'ancienne application.
5. Une fois seulement ces vérifications terminées, désinstaller l'application de signature différente, installer le nouvel APK et restaurer la sauvegarde via l'interface officielle.
6. Vérifier les réglages et les comptes. Certaines sessions peuvent demander une nouvelle connexion ; aucune restauration de compte n'est garantie.

Le projet ne fournit pas de commande qui désinstalle automatiquement votre application. Les sauvegardes contiennent potentiellement des identifiants de session : les garder privées.
