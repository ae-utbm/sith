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

Backend
-------

Python 3
~~~~~~~~

`Site officiel <https://www.python.org/>`__

Le python est un langage de programmation interprété multi paradigme sorti en 1991. Il est très populaire pour sa simplicité d'utilisation, sa puissance, sa stabilité, sécurité ainsi que sa grande communauté de développeur. Sa version 3, non rétro compatible avec sa version 2, a été publiée en 2008.

Django
~~~~~~

| `Site officiel <https://www.djangoproject.com/>`__
| `Documentation <https://docs.djangoproject.com/en/1.11/>`__

Django est un framework web pour Python apparu en 2005. Il fourni un grand nombre de fonctionnalités pour développer un site rapidement et simplement. Cela inclu entre autre un serveur Web de développement, un parseur d'URLs pour le routage des différentes URI du site, un ORM (Object-Relational Mapper) pour la gestion de la base de donnée ainsi qu'un moteur de templates pour le rendu HTML. Django propose une version LTS (Long Term Support) qui reste stable et est maintenu sur des cycles plus longs, ce sont ces versions qui sont utilisées.

PostgreSQL / SQLite
~~~~~~~~~~~~~~~~~~~

| `Site officiel PostgreSQL <https://www.postgresql.org/>`__
| `Site officiel SQLite <https://www.sqlite.org/index.html>`__

Comme la majorité des sites internet, le Sith de l'AE enregistre ses données dans une base de donnée. Nous utilisons une base de donnée relationnelle puisque c'est la manière typique d'utiliser Django et c'est ce qu'utilise son ORM. Dans la pratique il arrive rarement dans le projet de se soucier de ce qui fonctionne derrière puisque le framework abstrait les requêtes au travers de son ORM. Cependant, il arrive parfois que certaines requêtes, lorsqu'on cherche à les optimiser, ne fonctionnent que sur un seul backend.

Le principal à retenir ici est :

* Sur la version de production nous utilisons PostgreSQL, c'est cette version qui doit fonctionner en priorité
* Sur les versions de développement, pour faciliter l'installation du projet, nous utilisons la technologie SQLite qui ne requiert aucune installation spécifique. Certaines instructions ne sont pas supportées par cette technologie et il est parfois nécessaire d'installer PostgreSQL pour le développement de certaines parties du site.

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

C'est une vieille technologie et certains feront remarquer à juste titre que le Javascript moderne permet d'utiliser assez simplement la majorité de ce que fourni jQuery sans rien avoir à installer. Cependant, de nombreuses dépendances du projet utilisent encore jQuery qui est toujours très implanté aujourd'hui. Le sucre syntaxique qu'offre cette libraire reste très agréable à utiliser et économise parfois beaucoup de temps. Ça fonctionne et ça fonctionne très bien. C'est maintenu, léger et pratique, il n'y a pas de raison particulière de s'en séparer.

Sass
~~~~

`Site officiel <https://sass-lang.com/>`__

Sass (Syntactically Awesome Stylesheets) est un langage dynamique de génération de feuilles CSS apparu en 2006. C'est un langage de CSS "amélioré" qui permet l'ajout de variables (à une époque où le CSS ne les supportait pas), de fonctions, mixins ainsi qu'une syntaxe pour imbriquer plus facilement et proprement les règles sur certains éléments. Le Sass est traduit en CSS directement côté serveur et le client ne reçoit que du CSS.

C'est une technologie stable, mature et pratique qui ne nécessite pas énormément d'apprentissage.

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

Git est un logiciel de gestion de versions écrit par Linus Torsvald pour les besoins du noyau linux en 2005. C'est ce logiciel qui remplace svn anciennement utilisé pour gérer les sources du projet (rappelez vous, l'ancien site date d'avant 2005). Git est plus complexe à utiliser mais est bien plus puissant, permet de gérer plusieurs version en parallèle et génère des codebases vraiment plus légères puisque seules les modifications sont enregistrées (contrairement à svn qui garde une copie de la codebase par version).

GitLab
~~~~~~

| `Site officiel <https://about.gitlab.com/>`__
| `Instance de l'AE <https://ae-dev.utbm.fr/>`__

GitLab est une alternative libre à GitHub. C'est une plate-forme avec interface web permettant de déposer du code géré avec Git offrant également de l'intégration continue et du déploiement automatique.

C'est au travers de cette plate-forme que le Sith de l'AE est géré, sur une instance hébergée directement sur nos serveurs.

Virtualenv
~~~~~~~~~~

`Utiliser virtualenv <https://python-guide-pt-br.readthedocs.io/fr/latest/dev/virtualenvs.html>`__

Virtualenv est un utilitaire permettant d'installer un environnement Python de manière locale sans avoir besoin des droits root pour y installer des dépendances. Il est très utilisé pour gérer plusieurs projets différents en parallèles puisqu'il permet d'avoir sur sa machine plusieurs environnements différents et donc plusieurs versions d'une même dépendance dans plusieurs projets différent sans impacter le système sur lequel le tout est installé.

Black
~~~~~

`Site officiel <https://black.readthedocs.io/en/stable/>`__

Pour faciliter la lecture du code, il est toujours appréciable d'avoir une norme d'écriture cohérente. C'est généralement à l'étape de relecture des modifications par les autres contributeurs que sont repérées ces fautes de normes qui se doivent d'être corrigées pour le bien commun.

Imposer une norme est très fastidieux, que ce soit pour ceux qui relisent ou pour ceux qui écrivent. C'est pour cela que nous utilisons black qui est un formateur automatique de code. Une fois l'outil lancé, il parcours la codebase pour y repérer les fautes de norme et les corrige automatiquement sans que l'utilisateur ai à s'en soucier. Bien installé, il peut effectuer ce travail à chaque sauvegarde d'un fichier dans son éditeur, ce qui est très agréable pour travailler.