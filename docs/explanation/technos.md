Bien choisir ses technologies est crucial 
puisqu'une fois que le projet est suffisamment avancé,
il est très difficile voir impossible de revenir en arrière.

En novembre 2015, plusieurs choix se présentaient :

- Continuer avec du PHP
- S'orienter vers un langage web
plus moderne et à la mode comme le Python ou le Ruby
- Baser le site sur un framework Javascript

Le PHP 5, bientôt 7, de l'époque 
étant assez discutable comme 
[cet article le montre](https://eev.ee/blog/2012/04/09/php-a-fractal-of-bad-design/),
et l'ancien site ayant laissé un goût amer
à certains développeurs, celui-ci a été mis de côté.

L'écosystème Javascript étant à peine naissant 
et les frameworks allant et venant en seulement quelques mois,
il était impossible de prédire avec certitude 
si ceux-ci passeraient l'épreuve du temps,
il était inconcevable de tout parier là-dessus.

Ne restait plus que le Python et le Ruby 
avec les frameworks Django et Ruby On Rails.
Ruby ayant une réputation d'être très "cutting edge",
c'est Python, un langage bien implanté 
et ayant fait ses preuves, qui a été retenu.

Il est à noter que réécrire le site avec un framework PHP
comme Laravel ou Symphony eut aussi été possible, 
ces deux technologies étant assez matures et robustes
au moment où le développement a commencé.
Cependant, il aurait été potentiellement 
fastidieux de maintenir en parallèle deux
versions de PHP sur le serveur durant toute
la durée du développement.
Il faut aussi prendre en compte que nous étions 
à ce moment dégoûtés du PHP.

## Backend

### Python 3

[Site officiel](https://www.python.org/)

Le python est un langage de programmation
interprété multi paradigme sorti en 1991. 
Il est très populaire dans de nombreux domaines
pour sa simplicité d'utilisation,
sa polyvalence, sa sécurité ainsi
que sa grande communauté de développeur. 
Sa version 3, non rétro compatible avec sa version 2,
a été publiée en 2008.

!!!note

    Puisque toutes les dépendances du backend sont 
    des packages Python, 
    elles sont toutes ajoutées directement 
    dans le fichier **pyproject.toml**, 
    à la racine du projet.

### Django

[Site officiel](https://www.djangoproject.com/)

[Documentation](https://docs.djangoproject.com/en/latest/)

Django est un framework web pour Python apparu en 2005.
Il fournit un grand nombre de fonctionnalités
pour développer un site rapidement et simplement. 
Cela inclut entre autre un serveur Web de développement,
un parseur d'URLs pour le routage, 
un ORM (Object-Relational Mapper) 
pour la gestion de la base de donnée,
un cadre pour l'écriture et l'exécution des tests,
de nombreux utilitaires pour l'internationalisation,
les zones horaires et autres,
une interface web d'administration aisément configurable,
un moteur de templates pour le rendu HTML...

Django propose une version LTS (Long Term Support) 
qui reste stable et est maintenu sur des cycles plus longs.
Ce sont ces versions qui sont utilisées.


### PostgreSQL / SQLite3

[Site officiel PostgreSQL](https://www.postgresql.org/)

[Site officiel SQLite](https://www.sqlite.org/index.html>)

Comme la majorité des sites internet, 
le Sith de l'AE enregistre ses données 
dans une base de données. 
Nous utilisons une base de donnée relationnelle 
puisque c'est la manière typique d'utiliser 
Django et c'est ce qu'utilise son ORM.

Le principal à retenir ici est :

- Sur la version de production, nous utilisons PostgreSQL,
c'est cette version qui doit fonctionner en priorité.
C'est un système de gestion de base de données fiable,
puissant, activement maintenu, et particulièrement
bien supporté par Django.
- Sur les versions de développement,
pour faciliter l'installation du projet,
nous utilisons la technologie SQLite3 
qui ne requiert aucune installation spécifique
(la librairie `sqlite` est incluse dans les 
librairies par défaut de Python).
Certaines instructions ne sont pas supportées
par cette technologie et il est parfois nécessaire
d'installer PostgreSQL pour le développement 
de certaines parties du site 
(cependant, ces parties sont rares, et vous pourriez
même ne jamais en rencontrer une).

PostgreSQL est-ce avec quoi le site doit fonctionner.
Cependant, pour permettre aux développeurs
de travailler en installant le moins de dépendances
possible sur leur ordinateur,
il est également désirable de chercher la compatibilité
avec SQLite.
Aussi, dans la mesure du possible, nous
cherchons à ce que les interactions avec la base
de données fonctionnent avec l'un comme avec l'autre.

Heureusement, et grâce à l'ORM de Django, cette
double compatibilité est presque toujours possible.

## Frontend

### Jinja2

[Site officiel](https://jinja.palletsprojects.com/en/latest/)

Jinja2 est un moteur de template écrit en Python
qui s'inspire fortement de la syntaxe des templates de Django.
Ce moteur apporte toutefois son lot d'améliorations non négligeables. 
Il permet par exemple l'ajout de macros,
sortes de fonctions écrivant du HTML.

Un moteur de templates permet de générer 
du contenu textuel de manière procédural
en fonction des données à afficher,
cela permet de pouvoir inclure du code proche du Python
dans la syntaxe au milieu d'un document
contenant principalement du HTML. 
On peut facilement faire des boucles ou des conditions
ainsi même que de l'héritage de templates.

!!!note
    le rendu est fait côté serveur,
    si on souhaite faire des modifications côté client, 
    il faut utiliser du Javascript, rien ne change à ce niveau-là.

### jQuery

[Site officiel](https://jquery.com/)

jQuery est une bibliothèque JavaScript 
libre et multiplateforme créée pour faciliter
l'écriture de scripts côté client 
dans le code HTML des pages web. 
La première version est lancée en janvier 2006 par John Resig.

C'est une vieille technologie et certains
feront remarquer à juste titre que le Javascript 
moderne permet d'utiliser assez simplement 
la majorité de ce que fournit jQuery 
sans rien avoir à installer. 
Cependant, de nombreuses dépendances du projet
utilisent encore jQuery qui est toujours 
très implanté aujourd'hui. 
Le sucre syntaxique qu'offre cette librairie 
reste très agréable à utiliser et économise
parfois beaucoup de temps. 
Ça fonctionne et ça fonctionne très bien.
C'est maintenu et pratique.


### AlpineJS

[Site officiel](https://alpinejs.dev/)

AlpineJS est une librairie légère et minimaliste
permettant le rendu dynamique d'éléments sur une page
web, code de manière déclarative.
La librairie est décrite par ses créateurs comme :
"un outil robuste et minimal pour composer un comportement directement dans vos balises".

Alpine permet d'accomplir la plupart du temps le même résultat qu'un usage des fonctionnalités
de base des plus gros frameworks Javascript,
mais est beaucoup plus léger, un peu plus facile à prendre en main
et ne s'embarrasse pas d'un DOM virtuel.
Grâce à son architecture, il est extrêmement
bien adapté pour un usage dans un site multipage.
C'est une technologie simple et puissante qui se veut comme le jQuery du web moderne.

### Htmx

[Site officiel](https://htmx.org/)

En plus de AlpineJS, l’interactivité sur le site est augmentée via Htmx.
C'est une librairie js qui s'utilise également au moyen d'attributs HTML à
ajouter directement dans les templates.

Son principe est de remplacer certains éléments du html par un fragment de
HTML renvoyé par le serveur backend. Cela se marie très bien avec le
fonctionnement de django et en particulier de ses formulaires afin d'éviter
de doubler le travail pour la vérification des données.

### Sass

[Site officiel](https://sass-lang.com/)

Sass (Syntactically Awesome Stylesheets) est un langage dynamique 
de génération de feuilles CSS apparu en 2006.
C'est un langage de CSS "amélioré" qui permet 
l'ajout de variables 
(à une époque où le CSS ne les supportait pas),
de fonctions, mixins ainsi qu'une syntaxe pour 
imbriquer plus facilement et proprement les règles
sur certains éléments. 
Le Sass est traduit en CSS directement côté serveur 
et le client ne reçoit que du CSS.

C'est une technologie stable,
mature et pratique qui ne nécessite pas énormément
d'apprentissage.

### Fontawesome

[Site officiel](https://fontawesome.com>)

Fontawesome regroupe tout un ensemble 
d'icônes libres de droits utilisables facilement 
sur n'importe quelle page web.
Ils sont simples à modifier puisque modifiables 
via le CSS et présentent l'avantage de fonctionner
sur tous les navigateurs contrairement 
à un simple icône unicode qui s'affiche 
lui différemment selon la plate-forme.

!!!note

    C'est une dépendance capricieuse qui évolue très vite 
    et qu'il faut très souvent mettre à jour.

!!!warning

    Il a été décidé de **ne pas utiliser**
    de CDN puisque le site ralentissait régulièrement.
    Il est préférable de fournir cette dépendance avec le site.

## Workflow

### Git

[Site officiel](https://git-scm.com/)

Git est un logiciel de gestion de versions écrit par
Linus Torvalds pour les besoins du noyau linux en 2005. 
C'est ce logiciel qui remplace svn anciennement
utilisé pour gérer les sources du projet
(rappelez vous, l'ancien site date d'avant 2005).
Git est plus complexe à utiliser, 
mais est bien plus puissant,
permet de gérer plusieurs versions en parallèle 
et génère des codebases vraiment plus légères puisque 
seules les modifications sont enregistrées 
(contrairement à svn qui garde une copie 
de la codebase par version).

Git s'étant imposé comme le principal outil de gestion de versions,
sa communauté est très grande et sa documentation très fournie.
Il est également aisé de trouver des outils avec une interface graphique,
qui simplifient grandement son usage.

### GitHub

[Site officiel](https://github.com)

[Page github du Pôle Informatique de l'AE](https://github.com/ae-utbm/)

Github est un service web d'hébergement et de gestion de développement de logiciel.
C'est une plate-forme avec interface web permettant de déposer du code géré avec Git
offrant également de l'intégration continue et du déploiement automatique.
C'est au travers de cette plate-forme que le Sith de l'AE est géré.

### Sentry

[Site officiel](https://sentry.io)

[Instance de l'AE](https://ae2.utbm.fr)

Sentry est une plate-forme libre qui permet
de se tenir informé des bugs qui ont lieu sur le site.
À chaque crash du logiciel (erreur 500),
une erreur est envoyée sur la plate-forme
et il est indiqué précisément à quelle ligne de code
celle-ci a eu lieu, à quelle heure, combien de fois,
avec quel navigateur la page a été visitée et même éventuellement 
un commentaire de l'utilisateur qui a rencontré le bug.

C'est un outil incroyablement pratique
pour savoir tout ce qui ne fonctionne pas,
et surtout pour récolter toutes les informations
nécessaires à la réparation des bugs.

### Poetry

[Utiliser Poetry](https://python-poetry.org/docs/basic-usage/)

Poetry est un utilitaire qui permet de créer et gérer 
des environnements Python de manière simple et intuitive.
Il permet également de gérer et mettre à jour
le fichier de dépendances.

L'avantage d'utiliser poetry 
(et les environnements virtuels en général) 
est de pouvoir gérer plusieurs projets différents 
en parallèle puisqu'il permet d'avoir sur sa
machine plusieurs environnements différents et 
donc plusieurs versions d'une même dépendance 
dans plusieurs projets différents sans impacter 
le système sur lequel le tout est installé.

Poetry possède également l'avantage par rapport à un simple venv
que les versions exactes de toutes les dépendances,
y compris celles utilisées par d'autres dépendances,
sont consignées dans un fichier `.lock`.
On est donc sûr et certain que deux environnements virtuels
configurés avec le même fichier lock utiliseront
exactement les mêmes versions des mêmes dépendances,
y compris si celles-ci ne sont pas indiquées explicitement.

Les dépendances utilisées par poetry sont déclarées
dans le fichier `pyproject.toml`,
situé à la racine du projet.

### Ruff

[Site officiel](https://astral.sh/ruff)

Pour faciliter la lecture du code, 
il est toujours appréciable d'avoir 
une norme d'écriture cohérente.
C'est généralement à l'étape de relecture 
des modifications par les autres contributeurs 
que sont repérées ces fautes de normes 
qui se doivent d'être corrigées pour le bien commun.

Imposer une norme est très fastidieux,
que ce soit pour ceux qui relisent
ou pour ceux qui écrivent.
C'est pour cela que nous utilisons Ruff,
qui est un formateur et linter automatique de code.
Une fois l'outil lancé, il parcourt la codebase
pour y repérer les fautes de norme et les erreurs de logique courantes
et les corrige automatiquement (quand c'est possible)
sans que l'utilisateur ait à s'en soucier.
Bien installé, il peut effectuer ce travail
à chaque sauvegarde d'un fichier dans son éditeur,
ce qui est très agréable pour travailler.

### Biome

[Site officiel](https://biomejs.dev/)

Puisque Ruff ne fonctionne malheureusement que pour le Python,
nous utilisons Biome pour le javascript.

Biome est également capable d'analyser et formater les fichiers json et css.

Tout comme Ruff, Biome fait office de formateur et de linter.

### DjHTML

[Site officiel](https://github.com/rtts/djhtml)

Ruff permet de formater les fichiers Python et Biome les fichiers js,
mais ils ne formattent pas les templates et les feuilles de style.
Pour ça, il faut un autre outil, aisément intégrable
dans la CI : `djHTML`.

En utilisant conjointement Ruff, Biome et djHTML,
on arrive donc à la fois à formater les fichiers
Python et les fichiers relatifs au frontend.

### Npm

[Utiliser npm](https://docs.npmjs.com/cli/v6/commands/npm/)

Npm est un gestionnaire de paquets pour Node.js. C'est l'un des gestionnaires les plus répandus sur le marché et est très complet et utilisé.

Npm possède, tout comme Poetry, la capacité de locker les dépendances au moyen d'un fichier `.lock`. Il a également l'avantage de presque toujours être facilement disponible à l'installation.

Nous l'utilisons ici pour gérer les dépendances JavaScript. Celle-ci sont déclarées dans le fichier `package.json` situé à la racine du projet.

### Vite

[Utiliser vite](https://vite.dev)

Vite est un bundler de fichiers static. Il nous sert ici à mettre à disposition les dépendances frontend gérées par npm.

Il sert également à intégrer les autres outils JavaScript au workflow du Sith de manière transparente.

Vite a été choisi pour sa versatilité et sa popularité. Il est moderne et très rapide avec un fort soutien de la communauté.

Il intègre aussi tout le nécessaire pour la rétro-compatibilité et le Typescript.

Le logiciel se configure au moyen du fichier `vite.config.mts` à la racine du projet.
