# Configurer les Shorts à la télécommande

[Accueil](../README.fr.md) · [English](manual-setup.md) · **Français**

Ce tutoriel active les mêmes options de navigation et de lecture que notre script, directement dans **SmartTube officiel**. Tout se fait sur la TV, sans ordinateur ni ADB.

Les menus ci-dessous ont été vérifiés dans le code officiel **32.56 stable et bêta**. Les libellés peuvent varier dans d’autres versions ; les essais sur Fire TV restent à faire. Notez vos réglages actuels pour pouvoir les remettre ensuite.

Si vous utilisez plusieurs comptes, sélectionnez d’abord celui à configurer dans **Paramètres → Comptes**. Avec **Utiliser des paramètres distincts pour chaque compte**, répétez les réglages pour chaque compte souhaité ; sinon ils sont partagés.

## 1. Passer d’un Short à l’autre avec haut/bas

1. Depuis l’accueil, ouvrez **Paramètres → Général → Réaffectation des touches**.
2. Activez **Naviguer entre les Shorts avec les boutons haut/bas**.
3. Ouvrez un Short depuis une section Shorts et attendez que les commandes du lecteur disparaissent.

Le choix haut/bas désactive automatiquement la navigation Shorts gauche/droite. Il suffit d’activer l’option souhaitée.

**↓ Bas** passe au suivant ; **↑ Haut** revient au précédent lorsqu’il est disponible. Quand les commandes ou un menu sont affichés, les flèches servent à naviguer dans cette interface.

Choisissez bien l’option qui mentionne **Shorts** : celle des « vidéos standards » est un autre réglage. SmartTube remet aussi à zéro la réaffectation haut/bas associée quand vous changez cette option ; une action personnalisée sur ces touches peut donc être remplacée.

## 2. Enchaîner automatiquement à la fin du Short

1. Ouvrez **Paramètres → Lecteur vidéo → Divers** et **désactivez « Short en boucle »**.
2. Revenez dans **Lecteur vidéo → Mode de lecture** et choisissez **Lecture automatique de la vidéo suivante**.

Le deuxième réglage est une rubrique de **Lecteur vidéo**, distincte de **Divers**. Il s’applique aussi aux vidéos longues : elles pourront également s’enchaîner.

La navigation avec les flèches et l’enchaînement automatique sont indépendants. Vous pouvez garder haut/bas tout en remettant les Shorts en boucle.

## 3. Utiliser la liste de la section ouverte

Dans **Paramètres → Lecteur vidéo → Divers**, activez **Utiliser le contenu de la section actuelle comme playlist**. Retournez ensuite dans la section Shorts et ouvrez une vidéo depuis cette liste.

Cette option permet d’utiliser les vidéos de la section comme liste de lecture. Elle est facultative et concerne aussi les autres sections. Si une liste contient des vidéos classiques, elle ne devient pas une liste exclusivement composée de Shorts.

## Choisir une autre configuration ou revenir en arrière

| Vous souhaitez… | Réglage à modifier |
| --- | --- |
| Utiliser gauche/droite | Dans **Réaffectation des touches**, activez **Sauter les Shorts avec les boutons gauche/droite**. Haut/bas se désactive automatiquement. Droite = suivant ; gauche = précédent. |
| Désactiver les raccourcis Shorts | Décochez l’option de navigation Shorts actuellement activée dans ce même menu. |
| Répéter le Short en cours | Réactivez **Lecteur vidéo → Divers → Short en boucle**. |
| Ne plus utiliser la section comme playlist | Désactivez **Utiliser le contenu de la section actuelle comme playlist**. |
| Rétablir le comportement précédent des vidéos longues | Remettez votre choix initial dans **Lecteur vidéo → Mode de lecture**. |

Changer la navigation gauche/droite réinitialise aussi son affectation au volume. Pour annuler complètement vos changements, remettez les valeurs notées au départ, y compris les réaffectations personnalisées. Désactiver la lecture automatique des Shorts en réactivant leur boucle ne remet pas à lui seul le mode global de lecture à sa valeur précédente.

Pour **consulter** la configuration, revenez simplement dans ces menus : les cases cochées et le mode sélectionné indiquent les réglages actifs.

## Vérifier le résultat

Ouvrez un Short depuis une section Shorts contenant plusieurs vidéos. Testez bas puis haut avec les commandes masquées, et laissez un Short se terminer pour vérifier l’enchaînement. Fermez puis rouvrez SmartTube et vérifiez vos choix dans le même profil.

Si cela ne fonctionne pas, vérifiez le profil, les deux réglages de lecture automatique et l’origine de la vidéo : la navigation native dépend notamment de son appartenance à un groupe Shorts. Une vidéo verticale ouverte ailleurs n’est pas nécessairement reconnue de la même façon. La suite dépend des vidéos disponibles ; ces réglages ne garantissent pas un flux infini ni une suite composée uniquement de Shorts dans tous les contextes.

Ce parcours conserve l’application officielle. Il **n’ajoute ni le bouton de lecture automatique de Shorts Slider, ni notre préparation anticipée du Short suivant**.

---

Références : code officiel des [réaffectations](https://github.com/yuliskov/SmartTube/blob/32.56s/common/src/main/java/com/liskovsoft/smartyoutubetv2/common/app/presenters/settings/GeneralSettingsPresenter.java), des [réglages du lecteur](https://github.com/yuliskov/SmartTube/blob/32.56s/common/src/main/java/com/liskovsoft/smartyoutubetv2/common/app/presenters/settings/PlayerSettingsPresenter.java) et des [libellés français](https://github.com/yuliskov/SmartTube/blob/32.56s/common/src/main/res/values-fr/strings.xml).
