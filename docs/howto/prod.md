## Configurer Sentry

Pour connecter l'application à une instance de sentry (ex: https://sentry.io),
il est nécessaire de configurer la variable `SENTRY_DSN`
dans le fichier `settings_custom.py`.
Cette variable est composée d'un lien complet vers votre projet sentry.

## Récupérer les statiques

Nous utilisons du SCSS dans le projet.
En environnement de développement (`DEBUG=True`),
le SCSS est compilé à chaque fois que le fichier est demandé.
Pour la production, le projet considère 
que chacun des fichiers est déjà compilé et,
pour ce faire, il est nécessaire 
d'utiliser les commandes suivantes dans l'ordre :

```bash
python ./manage.py collectstatic # Pour récupérer tous les fichiers statiques
python ./manage.py compilestatic # Pour compiler les fichiers SCSS qu'ils contiennent
```

!!!tip

	Le dossier où seront enregistrés ces fichiers
    statiques peut être changé en modifiant la variable
    `STATIC_ROOT` dans les paramètres.