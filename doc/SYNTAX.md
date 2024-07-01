Cette page vise à documenter la syntaxe *Markdown* utilisée sur le site.

# Markdown-AE Documentation

Le Markdown le plus standard se trouve documenté ici:
https://www.markdownguide.org/basic-syntax.  
Si cette page n'est pas exhaustive vis à vis de la syntaxe du site AE,
elle a au moins le mérite de bien documenter le Markdown original.

Le réel parseur du site AE est une version tunée de [mistune](https://github.com/lepture/mistune).  
Les plus aventureux pourront aller lire ses [tests](https://github.com/lepture/mistune/blob/master/tests/fixtures)
afin d'en connaître la syntaxe le plus finement possible.  
En pratique, cette page devrait déjà résumer une bonne partie.

## Basique

- Mettre le texte en **gras** : `**texte**`
- Mettre le texte en *italique* : `*texte*`
- __Souligner__ le texte : `__texte__`
- ~~Barrer du texte~~ : `~~texte~~`
- On peut bien sûr tout ~~***__combiner__***~~ : `~~***__texte__***~~`
- Mettre du texte^en exposant^ : `<sup>texte</sup>`
- Mettre du texte~en indice~ : `<sub>texte</sub>`


## Liens

- Les liens simples sont détectés automatiquement : `http://www.site.com`

http://www.site.com

- Il est possible de nommer son lien : `[nom du lien](http://www.site.com)`

[nom du lien](http://www.site.com)

- Les liens peuvent être internes au site de l'AE, on peut dès lors éviter d'entrer
l'adresse complète d'une page : `[nom du lien](page://nomDeLaPage)`

[nom du lien](page://nomDeLaPage)

- On peut également utiliser une image pour les liens :
`[nom du lien]![images/imageDuSiteAE.png](/chemin/vers/image.png titre optionnel)(options)`

[nom du lien]![images/imageDuSiteAE.png](/chemin/vers/image.png titre optionnel)(options)



## Titres

- Plusieurs niveaux de titres sont possibles

```
# Titre de niveau 1
## Titre de niveau 2
### Titre de niveau 3
etc...
```
# Titre de niveau 1
## Titre de niveau 2
### Titre de niveau 3

## Paragraphes et sauts de ligne

Un nouveau paragraphe se fait avec deux retours à la ligne.

Un saut de ligne se force avec au moins deux espaces en fin de ligne.


## Listes

Il est possible de créer des listes :

### ordonnées :

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

1. élément
1. élément
1. élément


### non ordonnées :

```
- élément
- élément
- élément
```
- élément
- élément
- élément


## Tableaux

Un tableau est obtenu en respectant la syntaxe suivante :

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

L'alignement dans les cellules est géré comme suit, avec les ':' sur la ligne en dessous du titre:

```
|  Titre | Titre2 | Titre3 |
|:-------|:------:|-------:|
| gauche | centre | droite |
```
|  Titre | Titre2 | Titre3 |
|:-------|:------:|-------:|
| gauche | centre | droite |


## Images et contenus

Une image est insérée ainsi : `![texte alternatif](/chemin/vers/image.png "titre optionnel")`
![texte alternatif](/static/core/img/logo.png "titre optionnel")

On peut lui spécifier ses dimensions de plusieurs manières :

```
![image à 50%](/static/core/img/logo.png?50% "Image à 50%")
![image de 350 pixels de large](/static/core/img/logo.png?350 "Image de 350 pixels")
![image de 350x100 pixels](/static/core/img/logo.png?350x100 "Image de 350x100 pixels")
```


![image à 50%](/static/core/img/logo.png?50% "Image à 50%")  
Image à 50% de la largeur de la page.

![image de 350 pixels de large](/static/core/img/logo.png?350 "Image de 350 pixels")  
Image de 350 pixels de large.

![image de 350x100 pixels](/static/core/img/logo.png?350x100 "Image de 350x100 pixels")   
Image de 350x100 pixels.

(devrait pouvoir détecter si vidéo ou non)

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

## Note de bas de page

On les crée comme ça[^key]:

[^key]: ceci est le contenu de ma clef
```
Je fais une note[^clef].

[^clef]: je note ensuite où je veux le contenu de ma clef qui apparaîtra quand même en bas
```
Vous pouvez aussi utiliser des numéros pour nommer vos clefs.

```
Note plus complexe[^1]

[^1]:
    je peux même faire des blocs
    sur plusieurs lignes, comme d'habitude!
```

## Échapper des caractères

- Il est possible d'ignorer un caractère spécial en l'échappant à l'aide d'un \
- L'échappement de blocs de codes complet se fera à l'aide de balises <nosyntax></nosyntax>

## Autres (hérité de l'ancien wiki)

Une ligne peut être créée avec une ligne contenant 4 tirets (`----`).
