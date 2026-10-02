# SmartTube Shorts Slider

Les Shorts sur TV : réglages natifs ou bouton de lecture automatique.

[English](README.md) · **Français**

## 🎛️ Garder SmartTube officiel

La navigation entre Shorts et la lecture automatique sont déjà intégrées. Notre assistant aide à les configurer à partir d’une sauvegarde à restaurer sur la TV.

Collez la commande ci-dessous : elle vérifie Python et ADB, installe les prérequis manquants sur les systèmes pris en charge, puis lance l’assistant. Une autorisation système peut être demandée.

**Linux / macOS — Terminal**

```sh
sh -c 's=$(curl -fsSL https://raw.githubusercontent.com/valoche-68/SmartTube-Shorts-Slider/main/tools/start.sh) && sh -c "$s" sh "$@"' sh
```

**Windows — PowerShell**

```powershell
& ([scriptblock]::Create((Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/valoche-68/SmartTube-Shorts-Slider/main/tools/start.ps1').Content))
```

Menus en français · Version officielle **32.56 stable/bêta** · Aucun bouton ajouté au lecteur.

[Préparation, réglages manuels et annulation →](docs/user-guide.fr.md#smarttube-officiel)

## ▶️ Shorts Slider — notre version de SmartTube

Un APK personnalisé de SmartTube, avec deux ajouts pour les Shorts :

- **Bouton automatique dans le lecteur :** ON enchaîne, OFF met en boucle. Vous pouvez le masquer dans les réglages.
- **Préparation du suivant :** récupère à l’avance les informations de lecture du prochain Short. Désactivable.

**Sur un nouveau profil :** navigation haut/bas et lecture automatique activées, bouton visible et préparation du suivant active. Tout reste réglable ; vos choix sont conservés lors des mises à jour.

**[Télécharger la stable](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases/latest)** · **[Bêtas et toutes les versions](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases)**

[Installation, réglages et choix de l’APK →](docs/user-guide.fr.md#shorts-slider)

*Les essais sur Fire TV et les mesures de vitesse restent à faire.*

---

Basé sur [SmartTube](https://github.com/yuliskov/SmartTube) · [Construction et maintenance](docs/development.md) · [MIT](LICENSE)
