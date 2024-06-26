Configurer son environnement de développement
=============================================

Le projet n'est en aucun cas lié à un quelconque environnement de développement.
Il est possible pour chacun de travailler avec les outils dont il a envie et d'utiliser l'éditeur de code avec lequel il est le plus à l'aise.

Pour donner une idée, Skia a écrit une énorme partie de projet avec l'éditeur *Vim* sur du GNU/Linux
alors que Sli a utilisé *Sublime Text* sur MacOS et que Maréchal travaille avec PyCharm
sur ~~Windows muni de WSL~~ Arch Linux btw.

Configurer Ruff pour son éditeur
---------------------------------

.. note::

    Ruff est inclus dans les dépendances du projet.
    Si vous avez réussi à terminer l'installation, vous n'avez donc pas de configuration
    supplémentaire à effectuer.

Pour utiliser Ruff, placez-vous à la racine du projet et lancez la commande suivante :

.. code-block::

    ruff format  # pour formatter le code
    ruff check  # pour linter le code

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

VsCode
~~~~~~

Installez l'extension Ruff pour VsCode.
Ensuite, ajoutez ceci dans votre configuration :

.. sourcecode:: json

    {
        "[python]": {
            "editor.formatOnSave": true,
            "editor.defaultFormatter": "charliermarsh.ruff"
        }
    }

Sublime Text
~~~~~~~~~~~~

Vous devez installer ce plugin : https://packagecontrol.io/packages/LSP-ruff.
Suivez ensuite les instructions données dans la description du plugin.

Si vous utilisez le plugin `anaconda <http://damnwidget.github.io/anaconda/>`__, pensez à modifier les paramètres du linter pep8 pour éviter de recevoir des warnings dans le formatage de ruff comme ceci :

.. sourcecode:: json

    {
        "pep8_ignore": [
          "E203",
          "E266",
          "E501",
          "W503"
        ]
    }
