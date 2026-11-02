# SmartTube Shorts Slider

Notre version de SmartTube pour naviguer entre les Shorts et piloter leur lecture automatique sur TV.

[English](README.md) · **Français**

## ▶️ Ce que change notre APK

- **Bouton automatique avant « Qualité » :** ON enchaîne les Shorts disponibles, OFF répète le Short. Le bouton peut être masqué.
- **Navigation entre Shorts :** reconnaissance et choix du suivant adaptés, notamment depuis l’accueil. Les raccourcis natifs restent réglables.
- **Préparation du suivant :** récupère les informations de lecture d’un Short à l’avance, avec un cache séparé. Désactivable ; aucun gain de vitesse chiffré garanti.

**Sur un nouveau profil, tout est déjà activé :** navigation haut/bas, lecture automatique, bouton visible et préparation du suivant. Les mises à jour conservent vos choix existants.

**[Télécharger notre APK stable](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases/latest)** · [Bêta](https://github.com/valoche-68/SmartTube-Shorts-Slider/releases)

[Utilisation et réglages de Shorts Slider →](docs/manual-setup.fr.md) · [Installation et mises à jour →](docs/user-guide.fr.md#télécharger-et-mettre-à-jour)

## 📲 Installer notre APK par ADB

Collez une commande sur votre PC : elle vérifie Python et ADB, installe les prérequis manquants sur les systèmes pris en charge, puis vous guide pour installer la **stable Shorts Slider** sur la TV. Une autorisation système peut être demandée. L’application n’est pas lancée après installation.

**Linux / macOS — Terminal**

```sh
sh -c 's=$(curl -fsSL https://raw.githubusercontent.com/valoche-68/SmartTube-Shorts-Slider/main/tools/start.sh) && sh -c "$s" sh "$@"' sh
```

**Windows — PowerShell**

```powershell
& ([scriptblock]::Create((Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/valoche-68/SmartTube-Shorts-Slider/main/tools/start.ps1').Content))
```

[Mode d’emploi de l’installation →](docs/install.fr.md) · [Voir le script complet →](tools/install_slider.py)

*Essais Fire TV en cours. Le premier Short peut encore être long à charger ; la préparation du suivant ne prépare pas ce premier démarrage.*

---

Basé sur [SmartTube](https://github.com/yuliskov/SmartTube) · [Construction et maintenance](docs/development.md) · [MIT](LICENSE)
