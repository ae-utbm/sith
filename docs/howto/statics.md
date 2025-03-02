## C'est quoi les fichiers statics ?

Les fichiers statics sont tous les fichiers qui ne sont pas générés par le backend Django et qui sont téléchargés par le navigateur.
Cela comprend les fichiers css, javascript, images et autre.

La [documentation officielle](https://docs.djangoproject.com/fr/4.2/howto/static-files/) est très compréhensive.

Pour faire court, dans chaque module d'application il existe un dossier `static`
où mettre tous ces fichiers. Django se débrouille ensuite pour aller chercher
ce qu'il faut à l'intérieur.

Pour accéder à un fichier static dans un template Jinja il suffit d'utiliser la fonction `static`.

```jinja
	{# Exemple pour ajouter sith/core/static/core/base.css #}
    <link rel="stylesheet" href="{{ static('core/base.css') }}">
```

## L'intégration des scss

Les scss sont à mettre dans le dossier static comme le reste.
Il n'y a aucune différence avec le reste pour les inclure,
le système se débrouille automatiquement pour les transformer en `.css`

```jinja
	{# Exemple pour ajouter sith/core/static/core/base.scss #}
    <link rel="stylesheet" href="{{ static('core/style.scss') }}">
```

## L'intégration avec le bundler javascript

Le bundler javascript est intégré un peu différement. Le principe est très similaire mais
les fichiers sont à mettre dans un dossier `static/bundled` de l'application à la place.

Pour accéder au fichier, il faut utiliser `static` comme pour le reste mais en ajouter `bundled/` comme prefix.

```jinja
	{# Example pour ajouter sith/core/bundled/alpine-index.js #}
	<script type="module" src="{{ static('bundled/alpine-index.js') }}"></script>
	<script type="module" src="{{ static('bundled/other-index.ts') }}"></script>
```

!!!note
	
	Seuls les fichiers se terminant par `index.js` sont exportés par le bundler.
	Les autres fichiers sont disponibles à l'import dans le JavaScript comme
	si ils étaient tous au même niveau.

!!!warning

	Le bundler ne génère que des modules javascript.
	Ajouter `type="module"` n'est pas optionnel !

### Les imports au sein des fichiers des fichiers javascript bundlés

Pour importer au sein d'un fichier js bundlé, il faut préfixer ses imports de `#app:`.

Exemple:

```js
import { paginated } from "#core:utils/api";
```

## Comment ça fonctionne le post processing ?

Le post processing est géré par le module `staticfiles`. Les fichiers sont
compilés à la volée en mode développement.

Pour la production, ils sont compilés uniquement lors du `./manage.py collectstatic`.
Les fichiers générés sont ajoutés dans le dossier `staticfiles/generated`. Celui-ci est
ensuite enregistré comme dossier supplémentaire à collecter dans Django.