Cette page traite des conventions utilisées dans le développement du site.

## Langue

Les noms, de fonctions, de classe, de fichiers et de dossiers sont en anglais.
De même, les commentaires et les docstrings sont rédigés en anglais.

En revanche la documentation est rédigée en français.
En effet, les développeurs et les développeuses
qui ont été, sont et seront amenés à travailler
sur le site sont presque tous des francophones.
Or, la bonne compréhension prime.
Une documentation, qui se doit d'utiliser au mieux
les mots justes, compris de manière juste,
gagne à être écrite en langue vernaculaire,
lorsqu'on est assuré qu'une coopération
internationale est peu probable.

De la sorte, on s'assure au mieux que les
rédacteurs et rédactrices s'expriment bien
et que, réciproquement, les lecteurs et lectrices
comprennent au mieux.

A ce titre, on ne vous en voudra pas
si vous rédigez des commentaires ou des docstrings
en français.

En revanche, le code en lui-même doit
rester impérativement en anglais ;
les instructions étant en langue anglaise,
introduire des mots français au milieu crée un
contraste qui nuit à la compréhension.

De manière générale, demandez-vous juste à qui vous êtes en train d'écrire :

- si vous écrivez pour la machine, c'est en anglais
- si vous écrivez pour des êtres humains, c'est en français

## Gestion de version

Le projet utilise Git pour gérer les versions et 
GitHub pour héberger le dépôt distant.

L'arbre possède deux branches protégées : `master` et `taiste`.

`master` est la branche contenant le code tel qu'il
tourne effectivement sur le vrai site de l'AE.
Celle-ci doit, autant que faire se peut, rester impeccable.

`taiste` est la branche de référence pour le développement.
Cette dernière est régulièrement déployée sur le
site de test.
Elle permet de s'assurer que les diverses modifications
fonctionnent bien entre elles et fonctionnent bien
sur le serveur, avant d'être envoyées sur master.

### Gestion des branches

Toutes les modifications appliquées sur `taiste`
doivent se faire via des Pull Requests
depuis les différentes branches de développement.
Toutes les modifications appliquées sur `master`
doivent se faire via des Pull Requests
depuis `taiste`, ou bien depuis une branche
de *hotfix*, dans le cas où il faut réparer
un bug urgent apparu de manière impromptue.

Aucun `push` direct n'est admis, ni sur l'une,
ni sur l'autre branche.

En obligeant à passer par des PR,
on s'assure qu'au moins une autre personne
aura lu votre code et que les outils de test
et de vérification de code auront validé vos modifications.

Par extension du mode de travail par PR,
les branches `master` et `taiste` ne peuvent
recevoir du code que sous la forme de merge commits.

De plus, ces branches doivent recevoir, mais jamais donner
(à part entre elles).
Lorsqu'une modification a été effectuée sur `taiste`
et que vous souhaitez la récupérer dans une de vos
branches, vous devez procéder par `rebase`,
et non par `merge`.

En d'autres termes, vous devez respecter les deux règles suivantes :

1. Les branches `master` et `taiste` ne doivent contenir que des merge commits
2. Seules les branches `master` et `taiste` peuvent contenir des merge commits

=== "Bien ✔️"

    ```mermaid
    gitGraph:
        commit id: "initial commit"
        branch bar
        checkout main
        checkout bar
        commit id: "baz"
        checkout main
        merge bar id: "Merge branch bar"
        branch foo
        commit id: "foo a"
        commit id: "foo b"
        commit id: "foo c"
        checkout main
        merge foo id: "Merge branch foo"
    ```

=== "Pas bien ❌"

    ```mermaid
    gitGraph:
        commit
        branch bar
        branch foo
        commit id: "foo a"
        commit id: "foo b"
        checkout main
        checkout bar
        commit id: "baz"
        checkout main
        merge bar id: "Merge branch bar"
        checkout foo
        merge main id: "Merge branch main"
        commit id: "foo c"
        checkout main
        merge foo id: "Merge branch foo"
    ```

## Style de code

### Conventions de nommage

Les conventions de nommage sont celles de la
[PEP8](https://peps.python.org/pep-0008/) :

- les classes sont en PascalCase (ex: `class SacredGraal`)
- les constantes sont en MACRO_CASE (ex: `FAVOURITE_COLOUR = "blue"`)
- les fonctions et les variables sont en snake_case (ex: `swallow_origin = "african"`)
- les fichiers et dossiers contenant du code sont en snake_case
- les fichiers et les dossiers contenant de la documentation sont en kebab-case

En parallèle de la casse, les règles
de formatage du code sont celles du formateur Ruff.
Ces règles sont automatiquement appliquées quand 
vous faites tourner Ruff, donc vous n'avez pas à trop
vous poser de questions de ce côté-là.

En ce qui concerne les templates Jinja
et les fichiers SCSS, la norme de formatage
est celle par défaut de `djHTML`.

Pour Javascript, nous utilisons [standard](https://github.com/standard/standard).
C'est à la fois un formateur et un linter avec très peu de configuration,
un peu comme ruff.

!!!note "Le javascript dans les templates jinja"

    Standard n'est pas capable de lire dans les fichiers jinja,
    c'est sa principale limitation.

    Il est donc recommandé d'éviter de mettre trop de Javascript
    directement dans jinja mais de préférer des fichiers dédiés.


### Qualité du code

Pour s'assurer de la qualité du code, Ruff et Standard sont également utilisés.

Tout comme pour le format, Ruff et Standard ddoivent tourner avant chaque commit.

!!!note "to edit or not to edit"

    Vous constaterez sans doute que `ruff format` modifie votre code,
    mais que `ruff check` vous signale juste une liste
    d'erreurs sans rien modifier.

    En effet, `ruff format` ne s'occupe que de la forme du code,
    alors que `ruff check` regarde la logique du code.
    Si Ruff modifiait automatiquement la logique du code,
    ça serait un coup à introduire plus de bugs que ça n'en résoud.

    Il existe cependant certaines catégories d'erreurs que Ruff
    peut réparer de manière sûre.
    Pour appliquer ces réparations, faites :

    ```bash
    ruff check --fix
    ```

    Standard se comporte d'une manière très similaire

    ```bash
    npx standard # Liste toutes les erreurs et leurs catégories
    npx standard --fix # Applique tous les fix considérés safe et formatte le code
    ```


## Documentation

La documentation est écrite en markdown, avec les fonctionnalités
offertes par MkDocs, MkDocs-material et leurs extensions.

La documentation est intégralement en français, à l'exception
des exemples, qui suivent les conventions données plus haut.

### Découpage

La séparation entre les différentes parties de la documentation se fait
en suivant la méthodologie [Diataxis](https://diataxis.fr/).
On compte quatre sections :

1. Explications : parlez dans cette section de ce qui est bon à savoir
   sans que ça touche aux détails précis de l'implémentation.
   Si vous parlez de *pourquoi* un choix a été fait ou que vous montrez
   grossièrement les contours d'une partie du projet, c'est une explication.
2. Tutoriels : parlez dans cette section d'étapes précises
   ou de détails d'implémentation qu'un nouveau développeur
   doit suivre pour commencer à travailler sur le projet.
3. Utilisation : parlez dans cette section de méthodes utiles
   pour un développeur qui a déjà pris en main le projet.
   Voyez cette partie comme un livre de recettes de cuisine.
4. Référence : parlez dans cette section des détails d'implémentation du projet.
   En réalité, vous n'aurez pas besoin de beaucoup vous pencher dessus,
   puisque cette partie est composée presque uniquement
   des docstrings présents dans le code.

Pour plus de détails, lisez directement la documentation de Diataxis,
qui expose ces concepts de manière beaucoup plus complète.

### Style

Votre markdown doit être composé de lignes courtes ;
à partir de 88 caractères, c'est trop long.
Si une phrase est trop longue pour tenir sur une ligne,
vous pouvez l'écrire sur plusieurs.

Une ligne ne peut pas contenir plus d'une seule phrase.
Dit autrement, quand vous finissez une phrase,
faites systématiquement un saut de ligne.

=== "Bien ✔️"

    ```markdown linenums="1"
    First shalt thou take out the Holy Pin,
    then shalt thou count to three, no more, no less.
    Three shalt be the number thou shalt count,
    and the number of the counting shalt be three.
    Four shalt thou not count, neither count thou two,
    excepting that thou then proceed to three.
    Five is right out.
    Once the number three, being the third number, be reached,
    then lobbest thou thy Holy Hand Grenade of Antioch towards thou foe,
    who being naughty in My sight, shall snuff it.
    ```

=== "Pas bien ❌"

    ```markdown linenums="1"
    First shalt thou take out the Holy Pin, then shalt thou count to three, no more, no less. Three shalt be the number thou shalt count, and the number of the counting shalt be three. Four shalt thou not count, neither count thou two, excepting that thou then proceed to three. Five is right out. Once the number three, being the third number, be reached, then lobbest thou thy Holy Hand Grenade of Antioch towards thou foe, who being naughty in My sight, shall snuff it.
    ```

À noter que ces deux exemples donnent le même résultat
dans la documentation générée.
Mais la version avec de courtes lignes est beaucoup 
plus facile à modifier et à versioner.

!!!warning "Grammaire et orthographe"

    Ca peut paraitre évident dit comme ça, mais c'est toujours bon à rappeler :
    évitez de faire des fautes de français.
    Relisez vous quand vous avez fini d'écrire.


### Docstrings

Les docstrings sont écrits en suivant la norme
[Google](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)
et les fonctionnalités de [Griffe](https://mkdocstrings.github.io/griffe/docstrings/).

Ils doivent être explicites sur ce que la fonction accomplit,
mais ne pas parler de comment elle le fait.
Un bon docstring est celui qui dit exactement
ce qu'il faut pour qu'on puisse savoir comment
utiliser la fonction ou la classe documentée sans avoir à lire son code.

Tout comme les pédales d'une voiture :
pour pouvoir conduire, vous avez juste besoin
de savoir ce qui se passe quand vous appuyez dessus.
La connaissance de la mécanique interne est inutile dans ce cadre.

N'hésitez pas à mettre des examples dans vos docstrings.

## Pourquoi une partie du projet ne respecte pas ces conventions ?

Parce que le projet est vieux.
Le commit initial date du 18 novembre 2015.
C'était il y a presque dix ans au moment
où ces lignes sont écrites.
Au début, on ne se posait pas forcément
ce genre de questions.
Puis le projet a grandi, de manière sédimentaire,
fonctionnalité après fonctionnalité,
développé par des personnes n'ayant pas toutes la
même esthétique.

On retrouve dans le code ces inspirations diverses
de personnes variées à travers une décennie.
Au bout d'un moment, il est bon de se poser
et de normaliser les choses.

De ce côté-là, une première pierre a été posée
en novembre 2018, avec l'utilisation d'un formateur.
Il convient de poursuivre ce travail d'unification.

Cependant, là où on peut reformater automatiquement
du code, il faut y aller à la main pour retravailler
un style de code.
C'est un travail de fourmi qui prendra du temps.
