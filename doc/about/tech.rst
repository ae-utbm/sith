Technologies utilisées
======================

Bien choisir ses technologies est crucial puisqu'une fois que le projet est suffisamment avancé, il est très difficile voir impossible de revenir en arrière.

En novembre 2015, plusieurs choix s'offraient à nous :

* Continuer avec du PHP
* S'orienter vers un langage web plus moderne et à la mode comme le Python ou le Ruby
* Baser le site sur un framework Javascript

Le PHP 5, bientôt 7, de l'époque étant assez discutable comme `cet article <https://eev.ee/blog/2012/04/09/php-a-fractal-of-bad-design/>`__ et l'ancien site ayant laissé un goût amer à certains développeurs, celui-ci a été mis de côté.

L'écosystème Javascript étant à peine naissant et les frameworks allant et venant en seulement quelques mois, il était impossible de prédire avec certitude si ceux-ci passeraient l'épreuve du temps, il était inconcevable de tout parier là dessus.

Ne restait plus que le Python et le Ruby avec les frameworks Django et Ruby On Rails. Ruby ayant une réputation d'être très "cutting edge", c'est Python, un langage bien implanté et ayant fait ses preuves, qui a été retenu.

Il est à noter que réécrire le site avec un framework PHP comme Laravel ou Symphony
eut aussi été possible, ces deux technologies étant assez matures et robustes
au moment où le développement a commencé.
Cependant, il aurait été potentiellemet fastidieux de maintenir en parallèle deux
versions de PHP sur le serveur durant toute la durée du développement.
Il faut aussi prendre en compte que nous étions à ce moment dégoûtés du PHP.

Backend
-------

Python 3
~~~~~~~~

`Site officiel <https://www.python.org/>`__

Le python est un langage de programmation interprété multi paradigme sorti en 1991. Il est très populaire pour sa simplicité d'utilisation, sa puissance, sa stabilité, sécurité ainsi que sa grande communauté de développeur. Sa version 3, non rétro compatible avec sa version 2, a été publiée en 2008.

.. note::

    Puisque toutes les dépendances du backend sont des packages Python, elles sont toutes ajoutées directement dans le fichier **pyproject.toml** à la racine du projet.

Django
~~~~~~

| `Site officiel <https://www.djangoproject.com/>`__
| `Documentation <https://docs.djangoproject.com/en/1.11/>`__

Django est un framework web pour Python apparu en 2005. Il fourni un grand nombre de fonctionnalités pour développer un site rapidement et simplement. Cela inclu entre autre un serveur Web de développement, un parseur d'URLs pour le routage des différentes URI du site, un ORM (Object-Relational Mapper) pour la gestion de la base de donnée ainsi qu'un moteur de templates pour le rendu HTML. Django propose une version LTS (Long Term Support) qui reste stable et est maintenu sur des cycles plus longs, ce sont ces versions qui sont utilisées.

Il est possible que la version de Django utilisée ne soit pas la plus récente.
En effet, la version de Django utilisée est systématiquement celle munie d'un support au long-terme.

PostgreSQL / SQLite3
~~~~~~~~~~~~~~~~~~~

| `Site officiel PostgreSQL <https://www.postgresql.org/>`__
| `Site officiel SQLite <https://www.sqlite.org/index.html>`__

Comme la majorité des sites internet, le Sith de l'AE enregistre ses données dans une base de donnée. Nous utilisons une base de donnée relationnelle puisque c'est la manière typique d'utiliser Django et c'est ce qu'utilise son ORM. Dans la pratique il arrive rarement dans le projet de se soucier de ce qui fonctionne derrière puisque le framework abstrait les requêtes au travers de son ORM. Cependant, il arrive parfois que certaines requêtes, lorsqu'on cherche à les optimiser, ne fonctionnent que sur un seul backend.

Le principal à retenir ici est :

* Sur la version de production nous utilisons PostgreSQL, c'est cette version qui doit fonctionner en priorité
* Sur les versions de développement, pour faciliter l'installation du projet, nous utilisons la technologie SQLite3 qui ne requiert aucune installation spécifique (La librairie `sqlite` est incluse dans les librairies par défaut de Python). Certaines instructions ne sont pas supportées par cette technologie et il est parfois nécessaire d'installer PostgreSQL pour le développement de certaines parties du site.

Frontend
--------

Jinja2
~~~~~~

`Site officiel <https://jinja.palletsprojects.com/en/2.10.x/>`__

Jinja2 est un moteur de template écrit en Python qui s'inspire fortement de la syntaxe des templates de Django. Ce moteur apporte toutefois son lot d'améliorations non négligeables. Il permet par exemple l'ajout de macros, sortes de fonctions écrivant du HTML.

Un moteur de templates permet de générer du contenu textuel de manière procédural en fonction des données à afficher, cela permet de pouvoir inclure du code proche du Python dans la syntaxe au milieu d'un document contenant principalement du HTML. On peut facilement faire des boucles ou des conditions ainsi même que de l'héritage de templates.

Attention : le rendu est fait côté serveur, si on souhaite faire des modifications côté client, il faut utiliser du Javascript, rien ne change à ce niveau là.

Exemple d'utilisation d'un template Jinja2

.. sourcecode:: html+jinja

   <title>{% block title %}{% endblock %}</title>
   <ul>
   {% for user in users %}
     <li><a href="{{ user.url }}">{{ user.username }}</a></li>
   {% endfor %}
   </ul>

jQuery
~~~~~~

`Site officiel <https://jquery.com/>`__

jQuery est une bibliothèque JavaScript libre et multiplateforme créée pour faciliter l'écriture de scripts côté client dans le code HTML des pages web. La première version est lancée en janvier 2006 par John Resig.

C'est une vieille technologie et certains feront remarquer à juste titre que le Javascript moderne permet d'utiliser assez simplement la majorité de ce que fournit jQuery sans rien avoir à installer. Cependant, de nombreuses dépendances du projet utilisent encore jQuery qui est toujours très implanté aujourd'hui. Le sucre syntaxique qu'offre cette librairie reste très agréable à utiliser et économise parfois beaucoup de temps. Ça fonctionne et ça fonctionne très bien. C'est maintenu et pratique.

VueJS
~~~~~

`Site officiel <https://vuejs.org/>`__

jQuery permet de facilement manipuler le DOM et faire des requêtes en AJAX,
mais est moins pratique à utiliser pour créer des applications réactives.
C'est pour cette raison que Vue a été intégré au projet.

Vue est une librairie Javascript qui se concentre sur le rendu déclaratif et la composition des composants.
C'est une technologie très utilisée pour la création d'applications web monopages (ce que le site n'est pas)
mais son architecture progressivement adoptable permet aisément d'adapter son
comportement à une application multipage comme le site AE.

A ce jour, il est utilisé pour l'interface des barmen, dans l'application des comptoirs.

AlpineJS
~~~~~~~~

`Site officiel <https://alpinejs.dev/>`__

Dans une démarche similaire à celle de l'introduction de Vue, Alpine a aussi fait son
apparition au sein des dépendances Javascript du site.
La librairie est décrite par ses créateurs comme :
"un outil robuste et minimal pour composer un comportement directement dans vos balises".

Alpine permet d'accomplir la plupart du temps le même résultat qu'un usage des fonctionnalités
de base de Vue, mais est beaucoup plus léger, un peu plus facile à prendre en main
et ne s'embarasse pas d'un DOM virtuel.
De par son architecture, il extrêmement bien adapté pour un usage dans un site multipage.
C'est une technologie simple et puissante qui se veut comme le jQuery du web moderne.

Sass
~~~~

`Site officiel <https://sass-lang.com/>`__

Sass (Syntactically Awesome Stylesheets) est un langage dynamique de génération de feuilles CSS apparu en 2006. C'est un langage de CSS "amélioré" qui permet l'ajout de variables (à une époque où le CSS ne les supportait pas), de fonctions, mixins ainsi qu'une syntaxe pour imbriquer plus facilement et proprement les règles sur certains éléments. Le Sass est traduit en CSS directement côté serveur et le client ne reçoit que du CSS.

C'est une technologie stable, mature et pratique qui ne nécessite pas énormément d'apprentissage.

Fontawesome
~~~~~~~~~~~

`Site officiel <https://fontawesome.com>`__

Fontawesome regroupe tout un ensemble d'icônes libres de droits utilisables facilement sur n'importe quelle page web. Ils sont simple à modifier puisque modifiables via le CSS et présentent l'avantage de fonctionner sur tous les navigateurs contrairement à un simple icône unicode qui s'affiche lui différemment selon la plate-forme.

.. note::

    C'est une dépendance capricieuse qui évolue très vite et qu'il faut très souvent mettre à jour.

.. warning::

    Il a été décidé de **ne pas utiliser** de CDN puisque le site ralentissait régulièrement. Il est préférable de fournir cette dépendance avec le site.

Documentation
-------------

Sphinx
~~~~~~

`Site officiel <https://www.sphinx-doc.org/en/master/>`__

Sphinx est un outil qui permet la création de documentations intelligentes et très jolies. C'est cet outil qui permet d'écrire le documentation que vous êtes en train de lire actuellement. Développé en 2008 pour la communauté Python, c'est l'outil le plus répandu. Il est utilisé pour la documentation officielle de Python, pour celle de Django, Jinja2 et bien d'autres.

ReadTheDocs
~~~~~~~~~~~

`Site officiel <https://www.sphinx-doc.org/en/master/>`__

C'est un site d'hébergement de documentations utilisant Sphinx. Il propose la génération de documentation à partir de sources et leur hébergement gracieusement pour tout projet open source. C'est le site le plus utilisé et sur lequel sont hébergées bon nombre de documentations comme par exemple celle de Django. La documentation sur ce site est automatiquement générée à chaque nouvelle modification du projet.

reStructuredText
~~~~~~~~~~~~~~~~

`Site officiel <http://docutils.sourceforge.net/rst.html>`__

C'est un langage de balisage léger utilisé notamment dans la documentation du langage Python. C'est le langage dans lequel est écrit l'entièreté de la documentation ci-présente pour que Sphinx puisse la lire et la mettre en forme.

Workflow
--------

Git
~~~

`Site officiel <https://git-scm.com/>`__

Git est un logiciel de gestion de versions écrit par Linus Torvalds pour les besoins du noyau linux en 2005. C'est ce logiciel qui remplace svn anciennement utilisé pour gérer les sources du projet (rappelez vous, l'ancien site date d'avant 2005). Git est plus complexe à utiliser mais est bien plus puissant, permet de gérer plusieurs version en parallèle et génère des codebases vraiment plus légères puisque seules les modifications sont enregistrées (contrairement à svn qui garde une copie de la codebase par version).

Git s'étant imposé comme le principal outil de gestion de versions,
sa communauté est très grande et sa documentation très fournie.
Il est également aisé de trouver des outils avec une interface graphique,
qui simplifient grandement son usage.

GitHub
~~~~~~

| `Site officiel <https://github.com>`__
| `Page github d'AE-Dev <https://github.com/ae-utbm/>`__

Github est un service web d'hébergement et de gestion de développement de logiciel.
C'est une plate-forme avec interface web permettant de déposer du code géré avec Git
offrant également de l'intégration continue et du déploiement automatique.
C'est au travers de cette plate-forme que le Sith de l'AE est géré.

Depuis le 1er Octobre 2022, GitHub remplace GitLab dans un soucis de facilité d'entretien,
les machines sur lesquelles tournent le site étant de plus en plus vielles, il devenait très
difficile d'effectuer les mise à jours de sécurité du GitLab sans avoir de soucis matériel
pour l'hébergement et la gestion des projets informatiques de l'AE.

Sentry
~~~~~~

| `Site officiel <https://sentry.io>`__
| `Instance de l'AE <https://ae2.utbm.fr>`__

Sentry est une plate-forme libre qui permet de se tenir informer des bugs qui ont lieu sur le site. À chaque crash du logiciel (erreur 500), une erreur est envoyée sur la plate-forme et est indiqué précisément à quelle ligne de code celle-ci a eu lieu, à quelle heure, combien de fois, avec quel navigateur la page a été visitée et même éventuellement un commentaire de l'utilisateur qui a rencontré le bug.

Poetry
~~~~~~~~~~

`Utiliser Poetry <https://python-poetry.org/docs/basic-usage/>`__

Poetry est un utilitaire qui permet de créer et gérer des environements Python de manière simple et intuitive. Il permet également de gérer et mettre à jour le fichier de dépendances.
L'avantage d'utiliser poetry (et les environnements virtuels en général) est de pouvoir gérer plusieurs projets différents en parallèle puisqu'il permet d'avoir sur sa machine plusieurs environnements différents et donc plusieurs versions d'une même dépendance dans plusieurs projets différent sans impacter le système sur lequel le tout est installé.

Les dépendances utilisées par poetry sont déclarées dans le fichier `pyproject.toml`, situé à la racine du projet.

Black
~~~~~

`Site officiel <https://black.readthedocs.io/en/stable/>`__

Pour faciliter la lecture du code, il est toujours appréciable d'avoir une norme d'écriture cohérente. C'est généralement à l'étape de relecture des modifications par les autres contributeurs que sont repérées ces fautes de normes qui se doivent d'être corrigées pour le bien commun.

Imposer une norme est très fastidieux, que ce soit pour ceux qui relisent ou pour ceux qui écrivent. C'est pour cela que nous utilisons black qui est un formateur automatique de code. Une fois l'outil lancé, il parcours la codebase pour y repérer les fautes de norme et les corrige automatiquement sans que l'utilisateur n'ait à s'en soucier. Bien installé, il peut effectuer ce travail à chaque sauvegarde d'un fichier dans son éditeur, ce qui est très agréable pour travailler.