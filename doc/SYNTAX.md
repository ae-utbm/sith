Cette page vise à documenter la syntaxe *Markdown* utilisée sur le site.

# Markdown-AE Documentation


## Basique

* Mettre le texte en **gras** : `**texte**`

* Mettre le texte en *italique* : `*texte*`

* __Souligner__ le texte : `__texte__`

* ~~Barrer du texte~~ : `~~texte~~`

* ^Mettre du texte^ en ^exposant : `^mot` ou `^texte^`

* _Mettre du texte_ en _indice : `_mot` ou `_texte_`



## Liens

* Les liens simples sont détectés automatiquement : `http://www.site.com`

http://www.site.com

* Il est possible de nommer son lien : `[nom du lien](http://www.site.com)`

[nom du lien](http://www.site.com)

* Les liens peuvent être internes au site de l'AE, on peut dès lors éviter d'entrer
l'adresse complète d'une page : `[nom du lien](article://nomDeLaPage)`

[nom du lien](article://nomDeLaPage)

* On peut également utiliser une image pour les liens :
`[nom du lien]![images/imageDuSiteAE.png](/chemin/vers/image.png titre optionnel)(options)`

[nom du lien]![images/imageDuSiteAE.png](/chemin/vers/image.png titre optionnel)(options)



## Titres

* Plusieurs niveaux de titres sont possibles

```
# Titre de niveau 1
## Titre de niveau 2
### Titre de niveau 3
etc...
```
# Titre de niveau 1
## Titre de niveau 2
### Titre de niveau 3

Si le titre de votre section commence par un tilde (~) alors le texte sous la section est
affiché par défaut caché et il est consultable grace à un bouton +/-


## Listes

Il est possible de créer des listes :

* ordonnées :

```
1. élément
2. élément
3. élément
```
1. élément
1. élément
1. élément

Vous pouvez marquer plus simplement comme suit, les numéros se faisant tout seuls:
```
1. élément
1. élément
1. élément
```

* non ordonnées :
```
 * élément
 * élément
 * élément
```
* élément
* élément
* élément


## Tableaux

Un tableau est obtenu en respectant la syntax suivante :

```
| Titre | Titre2 | Titre3 |
|-------|--------|--------|
| test  | test   |   test |
| test  | test   |   test |
```
| Titre | Titre2 | Titre3 |
|-------|--------|--------|
| test  | test   |   test |
| test  | test   |   test |

L'alignement dans les cellules est géré en mettant des espaces à droite ou a gauche des chaines de caractères contenues dans chaque case.

```
| Titre | Titre2 | Titre3 |
|-------|--------|--------|
|gauche | centre |  droite|
```
| Titre | Titre2 | Titre3 |
|-------|--------|--------|
|gauche | centre |  droite|


## Images et contenus

Une image est insérée ainsi : `![texte alternatif](/chemin/vers/image.png "titre optionnel")(options)`
![texte alternatif](/static/core/img/logo.png "titre optionnel")(options)

( devrait pouvoir détecter si vidéo ou non )
( TODO : parametres )

## Blocs de citations

Un bloc de citation se crée ainsi :
```
> Ceci est
> un bloc de
> citation
```

> Ceci est
> un bloc de
> citation

Il est possible d'intégrer de la syntaxe Markdown-AE dans un tel bloc.



## échapper des caractères

* Il est possible d'ignorer un caractère spécial en l'échappant à l'aide d'un \
* L'échappement de blocs de codes complet se fera à l'aide de balises <nosyntax></nosyntax>



## Autres ( hérité de l'ancien wiki )

* Une ligne peut être crée avec une ligne contenant 4 tirets ( - ).
* Une barre de progression est crée ainsi :
> [[[70]]]
* Notes en pied de page :
> ((note))


