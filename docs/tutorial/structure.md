## La structure d'un projet Django

Un projet Django est structuré en applications.
Une application est un package Python 
contenant un ensemble de vues, de modèles, de templates, etc.
Sémantiquement, une application représente 
un ensemble de fonctionnalités cohérentes.
Par exemple, dans notre cas, nous avons une application
chargée de la gestion des comptoirs, une autre de la gestion
des clubs, une autre de la gestion du SAS, etc.

On trouve généralement dans un projet Django
une application principale qui contient les
fichiers de configuration du projet, 
les urls et éventuellement des commandes d'administration.

## Arborescence du projet

Le code source du projet est organisé comme suit :

<div class="annotate">
```
sith3/
├── .github/
│   ├── actions/ (1)
│   └── workflows/ (2)
├── accounting/ (3)
│   └── ...
├── api/ (4)
│   └── ...
├── club/ (5)
│   └── ...
├── com/ (6)
│   └── ...
├── core/ (7)
│   └── ...
├── counter/ (8)
│   └── ...
├── docs/ (9)
│   └── ...
├── eboutic/ (10)
│   └── ...
├── election/ (11)
│   └── ...
├── forum/ (12)
│   └── ...
├── galaxy/ (13)
│   └── ...
├── launderette/ (14)
│   └── ...
├── locale/ (15)
│   └── ...
├── matmat/ (16)
│   └── ...
├── pedagogy/ (17)
│   └── ...
├── rootplace/ (18)
│   └── ...
├── sas/ (19)
│   └── ...
├── sith/ (20)
│   └── ...
├── stock/ (21)
│   └── ...
├── subscription/ (22)
│   └── ...
├── trombi/ (23)
│   └── ...
│
├── .coveragerc (24)
├── .envrc (25)
├── .gitattributes
├── .gitignore
├── .mailmap
├── .env.exemple
├── manage.py (26)
├── mkdocs.yml (27)
├── poetry.lock
├── pyproject.toml (28)
└── README.md
```
</div>

1. Dossier contenant certaines actions réutilisables
   dans des workflows Github. Par exemple, l'action
   `setup-project` installe poetry puis appelle
   la commande `poetry install`.
2. Dossier contenant les fichiers de configuration
   des workflows Github. 
   Par exemple, le workflow `docs.yml` compile
   et publie la documentation à chaque push sur la branche `master`.
3. Application de gestion de la comptabilité.
4. Application contenant des routes d'API.
5. Application de gestion des clubs et de leurs membres.
6. Application contenant les fonctionnalités 
   destinées aux responsables communication de l'AE.
7. Application contenant la modélisation centrale du site.
   On en reparle plus loin sur cette page.
8. Application de gestion des comptoirs, des permanences
   sur ces comptoirs et des transactions qui y sont effectuées.
9. Dossier contenant la documentation.
10. Application de gestion de la boutique en ligne.
11. Application de gestion des élections.
12. Application de gestion du forum
13. Application de gestion de la galaxie ; la galaxie
    est un graphe des niveaux de proximité entre les différents
    étudiants.
14. Gestion des machines à laver de l'AE
15. Dossier contenant les fichiers de traduction.
16. Fonctionnalités de recherche d'utilisateurs.
17. Le guide des UEs du site, sur lequel les utilisateurs
    peuvent également laisser leurs avis.
18. Fonctionnalités utiles aux utilisateurs root.
19. Le SAS, où l'on trouve toutes les photos de l'AE.
20. Application principale du projet, contenant sa configuration.
21. Gestion des stocks des comptoirs.
22. Gestion des cotisations des utilisateurs du site.
23. Gestion des trombinoscopes.
24. Fichier de configuration de coverage.
25. Fichier de configuration de direnv.
26. Fichier généré automatiquement par Django. C'est lui
    qui permet d'appeler des commandes de gestion du projet
    avec la syntaxe `python ./manage.py <nom de la commande>`
27. Le fichier de configuration de la documentation,
    avec ses plugins et sa table des matières.
28. Le fichier où sont déclarés les dépendances et la configuration
    de certaines d'entre elles.
    

## L'application principale

L'application principale du projet est le package `sith`.
Ce package contient les fichiers de configuration du projet,
la racine des urls.

Il est organisé comme suit :

<div class="annotate">
```
sith/
├── settings.py (1)
├── settings_custom.py (2)
├── toolbar_debug.py (3)
├── urls.py (4)
└── wsgi.py (5)
```
</div>

1. Fichier de configuration du projet.
   Ce fichier contient les paramètres de configuration du projet.
   Par exemple, il contient la liste des applications
   installées dans le projet.
2. Configuration maison pour votre environnement.
   Toute variable que vous définissez dans ce fichier sera prioritaire
   sur la configuration donnée dans `settings.py`.
3. Configuration de la barre de debug.
   C'est inutilisé en prod, mais c'est très pratique en développement.
4. Fichier de configuration des urls du projet.
5. Fichier de configuration pour le serveur WSGI.
   WSGI est un protocole de communication entre le serveur
   et les applications.
   Ce fichier ne vous servira sans doute pas sur un environnement
   de développement, mais il est nécessaire en production.

## Les applications

Les applications sont des packages Python.
Dans ce projet, les applications sont généralement organisées
comme suit :

<div class="annotate">
```
.
├── migrations/ (1)
│   └── ...
├── templates/ (2)
│   └── ...
├── admin.py (3)
├── models.py (4)
├── tests.py (5)
├── urls.py (6)
└── views.py (7)
```
</div>

1. Dossier contenant les migrations de la base de données.
   Les migrations sont des fichiers Python qui permettent
   de mettre à jour la base de données.
   cf. [Gestion des migrations](../howto/migrations.md)
2. Dossier contenant les templates jinja utilisés par cette application.
3. Fichier de configuration de l'interface d'administration.
   Ce fichier permet de déclarer les modèles de l'application
   dans l'interface d'administration.
4. Fichier contenant les modèles de l'application.
   Les modèles sont des classes Python qui représentent
   les tables de la base de données.
5. Fichier contenant les tests de l'application.
6. Configuration des urls de l'application.
7. Fichier contenant les vues de l'application.
   Dans les plus grosses applications,
   ce fichier peut être remplacé par un package
   `views` dans lequel les vues sont réparties entre
   plusieurs fichiers.

L'organisation peut éventuellement être un peu différente
pour certaines applications, mais le principe
général est le même.