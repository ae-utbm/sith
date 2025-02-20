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
sith/
├── .github/
│   ├── actions/ (1)
│   └── workflows/ (2)
├── accounting/ (3)
│   └── ...
├── club/ (4)
│   └── ...
├── com/ (5)
│   └── ...
├── core/ (6)
│   └── ...
├── counter/ (7)
│   └── ...
├── docs/ (8)
│   └── ...
├── eboutic/ (9)
│   └── ...
├── election/ (10)
│   └── ...
├── forum/ (11)
│   └── ...
├── galaxy/ (12)
│   └── ...
├── launderette/ (13)
│   └── ...
├── locale/ (14)
│   └── ...
├── matmat/ (15)
│   └── ...
├── pedagogy/ (16)
│   └── ...
├── rootplace/ (17)
│   └── ...
├── sas/ (18)
│   └── ...
├── sith/ (19)
│   └── ...
├── subscription/ (20)
│   └── ...
├── trombi/ (21)
│   └── ...
├── antispam/ (22)
│   └── ...
├── staticfiles/ (23)
│   └── ...
├── processes/ (24)
│   └── ...
│
├── .coveragerc (25)
├── .envrc (26)
├── .gitattributes
├── .gitignore
├── .mailmap
├── .env (27)
├── .env.example (28)
├── manage.py (29)
├── mkdocs.yml (30)
├── uv.lock
├── pyproject.toml (31)
├── .venv/ (32)
├── .python-version (33)
├── Procfile.dev (34)
├── Procfile.pytest (35)
└── README.md
```
</div>

1. Dossier contenant certaines actions réutilisables
   dans des workflows Github. Par exemple, l'action
   `setup-project` installe uv puis appelle
   configure l'environnement de développement
2. Dossier contenant les fichiers de configuration
   des workflows Github. 
   Par exemple, le workflow `docs.yml` compile
   et publie la documentation à chaque push sur la branche `master`.
3. Application de gestion de la comptabilité.
4. Application de gestion des clubs et de leurs membres.
5. Application contenant les fonctionnalités 
   destinées aux responsables communication de l'AE.
6. Application contenant la modélisation centrale du site.
   On en reparle plus loin sur cette page.
7. Application de gestion des comptoirs, des permanences
   sur ces comptoirs et des transactions qui y sont effectuées.
8. Dossier contenant la documentation.
9. Application de gestion de la boutique en ligne.
10. Application de gestion des élections.
11. Application de gestion du forum
12. Application de gestion de la galaxie ; la galaxie
    est un graphe des niveaux de proximité entre les différents
    étudiants.
13. Gestion des machines à laver de l'AE
14. Dossier contenant les fichiers de traduction.
15. Fonctionnalités de recherche d'utilisateurs.
16. Le guide des UEs du site, sur lequel les utilisateurs
    peuvent également laisser leurs avis.
17. Fonctionnalités utiles aux utilisateurs root.
18. Le SAS, où l'on trouve toutes les photos de l'AE.
19. Application principale du projet, contenant sa configuration. 
20. Gestion des cotisations des utilisateurs du site. 
21. Outil pour faciliter la fabrication des trombinoscopes de promo. 
22. Fonctionnalités pour gérer le spam. 
23. Gestion des statics du site. Override le système de statics de Django.
    Ajoute l'intégration du scss et du bundler js
    de manière transparente pour l'utilisateur. 
24. Module de gestion des services externes.
    Offre une API simple pour utiliser les fichiers `Procfile.*`.
25. Fichier de configuration de coverage. 
26. Fichier de configuration de direnv. 
27. Contient les variables d'environnement, qui sont susceptibles
    de varier d'une machine à l'autre.
28. Contient des valeurs par défaut pour le `.env`
    pouvant convenir à un environnment de développement local
29. Fichier généré automatiquement par Django. C'est lui
    qui permet d'appeler des commandes de gestion du projet
    avec la syntaxe `python ./manage.py <nom de la commande>`
30. Le fichier de configuration de la documentation,
    avec ses plugins et sa table des matières. 
31. Le fichier où sont déclarés les dépendances et la configuration
    de certaines d'entre elles.
32. Dossier d'environnement virtuel généré par uv
33. Fichier qui contrôle quelle version de python utiliser pour le projet
34. Fichier qui contrôle les services additionnels à lancer
    avec le serveur de développement   
35. Fichier qui contrôle les services additionnels à lancer
    avec pytest

## L'application principale

L'application principale du projet est le package `sith`.
Ce package contient les fichiers de configuration du projet,
la racine des urls.

Il est organisé comme suit :

<div class="annotate">
```
sith/
├── settings.py (1)
├── toolbar_debug.py (2)
├── urls.py (3)
└── wsgi.py (4)
```
</div>

1. Fichier de configuration du projet.
   Ce fichier contient les paramètres de configuration du projet.
   Par exemple, il contient la liste des applications
   installées dans le projet.
2. Configuration de la barre de debug.
   C'est inutilisé en prod, mais c'est très pratique en développement.
3. Fichier de configuration des urls du projet.
4. Fichier de configuration pour le serveur WSGI.
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
├── static/ (3)
│   └── bundled/ (4)
│   └── ...
├── api.py (5)
├── admin.py (6)
├── models.py (7)
├── tests.py (8)
├── schemas.py (9)
├── urls.py (10)
└── views.py (11)
```
</div>

1. Dossier contenant les migrations de la base de données.
   Les migrations sont des fichiers Python qui permettent
   de mettre à jour la base de données.
   cf. [Gestion des migrations](../howto/migrations.md)
2. Dossier contenant les templates jinja utilisés par cette application.
3. Dossier contenant les fichiers statics (js, css, scss) qui sont récpérée par Django.
4. Dossier contenant du js qui sera process avec le bundler javascript. Le contenu sera automatiquement process et accessible comme si ça avait été placé dans le dossier `static/bundled`.
5. Fichier contenant les routes d'API liées à cette application
6. Fichier de configuration de l'interface d'administration.
   Ce fichier permet de déclarer les modèles de l'application
   dans l'interface d'administration.
7. Fichier contenant les modèles de l'application.
   Les modèles sont des classes Python qui représentent
   les tables de la base de données.
8. Fichier contenant les tests de l'application.
9. Schémas de validation de données utilisés principalement dans l'API.
10. Configuration des urls de l'application.
11. Fichier contenant les vues de l'application.
   Dans les plus grosses applications,
   ce fichier peut être remplacé par un package
   `views` dans lequel les vues sont réparties entre
   plusieurs fichiers.

L'organisation peut éventuellement être un peu différente
pour certaines applications, mais le principe
général est le même.
