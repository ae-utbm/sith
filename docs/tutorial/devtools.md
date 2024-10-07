Le projet n'est en aucun cas lié à un
quelconque environnement de développement.
Il est possible pour chacun de travailler 
avec les outils dont il a envie et d'utiliser
l'éditeur de code avec lequel il est le plus à l'aise.

Pour donner une idée, Skia a écrit une énorme
partie de projet avec l'éditeur *Vim* sur du GNU/Linux
alors que Sli a utilisé *Sublime Text* sur MacOS 
et que Maréchal travaille avec PyCharm
sur ~~Windows muni de WSL~~ Arch Linux btw.

## Configurer les pre-commit hooks

La procédure habituelle pour contribuer au
projet consiste à commit des modifications, 
puis à les push sur le dépôt distant et 
à ouvrir une pull request. 
Cette PR va faire tourner les outils de vérification 
de la qualité de code. 
Si la vérification échoue, la PR est bloquée,
et il faut réparer le problème 
(ce qui implique de push un micro-commit 
ou de push force sur la branche).

Dans l'idéal, on aimerait donc qu'il soit
impossible d'oublier de faire tourner ces vérifications.
Pour ça, il existe un mécanisme : les pre-commits hooks.
Ce sont des actions qui tournent automatiquement
lorsque vous effectuez un `git commit`.
Ces dernières vont analyser et éventuellement modifier le code,
avant que Git n'ajoute effectivement le commit sur l'arbre git.
Voyez ça comme une micro-CI qui tourne en local.

Les git hooks sont une fonctionnalité par défaut de Git. 
Cependant, leur configuration peut-être un peu 
embêtante si vous le faites manuellement.
Pour gérer ça plus simplement,
nous utilisons le logiciel python [pre-commit](https://pre-commit.com/)
qui permet de contrôler leur installation via un seul fichier de configuration,
placé à la racine du projet
(plus précisément, il s'agit du fichier `.pre-commit-config.yaml`).

!!!note

    Les pre-commits sont également utilisés dans la CI.
    Si ces derniers fonctionnent localement, vous avez la garantie que la pipeline ne sera pas fachée. ;)

C'est une fonctionnalité de git lui-même,
mais c'est assez embêtant à gérer manuellement.
Pour gérer ça plus simplement, 
nous utilisons le logiciel python [pre-commit](https://pre-commit.com/)
qui permet de contrôller leur installation via un fichier yaml.

Le logiciel est installé par défaut par poetry. 
Il suffit ensuite de lancer :

```bash
pre-commit install
```
Une fois que vous avez fait cette commande, pre-commit
tournera automatiquement chaque fois que vous ferez
un nouveau commit.

Il est également possible d'appeler soi-même les pre-commits :

```bash
pre-commit run --all-files
```


## Configurer Ruff pour son éditeur

!!!note

    Ruff est inclus dans les dépendances du projet.
    Si vous avez réussi à terminer l'installation, vous n'avez donc pas de configuration
    supplémentaire à effectuer.

Pour utiliser Ruff, placez-vous à la racine du projet et lancez la commande suivante :

```bash
ruff format  # pour formatter le code
ruff check  # pour linter le code
```

Ruff va alors faire son travail sur l'ensemble du projet puis vous dire
si des documents ont été reformatés (si vous avez fait `ruff format`)
ou bien s'il y a des erreurs à réparer (si vous avez faire `ruff check`).

Appeler Ruff en ligne de commandes avant de pousser votre code sur Github
est une technique qui marche très bien.
Cependant, vous risquez de souvent l'oublier.
Or, lorsque le code ne respecte pas les standards de qualité,
la pipeline bloque les PR sur les branches protégées.

Pour éviter de vous faire régulièrement avoir, vous pouvez configurer
votre éditeur pour que Ruff fasse son travail automatiquement à chaque édition d'un fichier.
Nous tenterons de vous faire ici un résumé pour deux éditeurs de textes populaires
que sont VsCode et Sublime Text.

=== "VsCode"

    Installez l'extension Ruff pour VsCode.
    Ensuite, ajoutez ceci dans votre configuration :

    ```json
    {
        "[python]": {
            "editor.formatOnSave": true,
            "editor.defaultFormatter": "charliermarsh.ruff"
        }
    }
    ```

=== "Sublime Text"

    Vous devez installer le plugin [LSP-ruff](https://packagecontrol.io/packages/LSP-ruff).
    Suivez ensuite les instructions données dans la description du plugin.

    Dans la configuration de votre projet, ajoutez ceci:

    ```json
    {
        "settings": {
            "lsp_format_on_save": true, // Commun à ruff et biome
            "LSP": { 
                "LSP-ruff": {
                    "enabled": true,
                }
            }
        }
    }
    ```

    Si vous utilisez le plugin [anaconda](http://damnwidget.github.io/anaconda/),
    pensez à modifier les paramètres du linter pep8
    pour éviter de recevoir des warnings dans le formatage 
    de ruff comme ceci :

    ```json
    {
        "pep8_ignore": [
          "E203",
          "E266",
          "E501",
          "W503"
        ]
    }
    ```

## Configurer Biome pour son éditeur

!!!note

    Biome est inclus dans les dépendances du projet.
    Si vous avez réussi à terminer l'installation, vous n'avez donc pas de configuration
    supplémentaire à effectuer.

Pour utiliser Biome, placez-vous à la racine du projet et lancer la commande suivante:

```bash
    npx @biomejs/biome check # Pour checker le code avec le linter et le formater
    npx @biomejs/biome check --write # Pour appliquer les changemnts
```

Biome va alors faire son travail sur l'ensemble du projet puis vous dire
si des documents ont été reformatés (si vous avez fait `npx @biomejs/biome format --write`)
ou bien s'il y a des erreurs à réparer (si vous avez faire `npx @biomejs/biome lint`) ou les deux (si vous avez fait `npx @biomejs/biome check --write`).

Appeler Biome en ligne de commandes avant de pousser votre code sur Github
est une technique qui marche très bien.
Cependant, vous risquez de souvent l'oublier.
Or, lorsque le code ne respecte pas les Biomes de qualité,
la pipeline bloque les PR sur les branches protégées.

Pour éviter de vous faire régulièrement avoir, vous pouvez configurer
votre éditeur pour que Biome fasse son travail automatiquement à chaque édition d'un fichier.
Nous tenterons de vous faire ici un résumé pour deux éditeurs de textes populaires
que sont VsCode et Sublime Text.

=== "VsCode"

    Biome est fourni par le plugin [Biome](https://marketplace.visualstudio.com/items?itemName=biomejs.biome).

    Ensuite, ajoutez ceci dans votre configuration :

    ```json
    {
      "editor.defaultFormatter": "<other formatter>",
      "[javascript]": {
        "editor.defaultFormatter": "biomejs.biome"
      }
    }
    ```

=== "Sublime Text"

    Tout comme pour ruff, il suffit d'installer un plugin lsp [LSP-biome](https://packagecontrol.io/packages/LSP-biome).

    Et enfin, dans la configuration de votre projet, ajouter les lignes suivantes :

    ```json
    {
        "settings": {
            "lsp_format_on_save": true, // Commun à ruff et biome
            "LSP": { 
                "LSP-biome": {
                    "enabled": true,
                }
            }
        }
    }
    ```