## Configurer Sentry

Pour connecter l'application à une instance de sentry (ex: https://sentry.io),
il est nécessaire de configurer la variable `SENTRY_DSN`
dans le fichier `.env`.
Cette variable est composée d'un lien complet vers votre projet sentry.

## Récupérer les statiques

Nous utilisons du SCSS dans le projet.
En environnement de développement (`DEBUG=true`),
le SCSS est compilé à chaque fois que le fichier est demandé.
Pour la production, le projet considère 
que chacun des fichiers est déjà compilé.
C'est pourquoi le SCSS est automatiquement compilé lors 
de la récupération des fichiers statiques.
Les fichiers JS sont également automatiquement minifiés.

Il peut être judicieux de supprimer les anciens fichiers
statiques avant de collecter les nouveaux.
Pour ça, ajoutez le flag `--clear` à la commande `collectstatic` :

```bash
python ./manage.py collectstatic --clear
```

!!!tip

	Le dossier où seront enregistrés ces fichiers
    statiques peut être changé en modifiant la variable
    `STATIC_ROOT` dans les paramètres.
