Configurer son environnement de développement
=============================================

Le projet n'est en aucun cas lié à un quelconque environnement de développement. Il est possible pour chacun de travailler avec les outils dont il a envie et d'utiliser l'éditeur de code avec lequel il est le plus à l'aise.

Pour donner une idée, Skia a écrit une énorme partie de projet avec l'éditeur *Vim* sur du GNU/Linux
alors que Sli a utilisé *Sublime Text* sur MacOS et que Maréchal travaille avec PyCharm
sur Windows muni de WSL.

Configurer Black pour son éditeur
---------------------------------

.. note::

    Black est inclus dans les dépendances du projet.
    Si vous avez réussi à terminer l'installation, vous n'avez donc pas de configuration
    supplémentaire à effectuer.

Pour utiliser Black, placez-vous à la racine du projet et lancez la commande suivante :

.. code-block::

    black .

Black va alors faire son travail sur l'ensemble du projet puis vous dire quels documents
ont été reformatés.

Appeler Black en ligne de commandes avant de pousser votre code sur Github
est une technique qui marche très bien.
Cependant, vous risquez de souvent l'oublier.
Or, lorsque le code est mal formaté, la pipeline bloque les PR sur les branches protégées.

Pour éviter de vous faire régulièrement blacked, vous pouvez configurer
votre éditeur pour que Black fasse son travail automatiquement à chaque édition d'un fichier.
Nous tenterons de vous faire ici un résumé pour deux éditeurs de textes populaires
que sont VsCode et Sublime Text.

VsCode
~~~~~~

.. warning::

    Il faut installer black dans son environement virtuel pour cet éditeur

Black est directement pris en charge par l'extension pour le Python de VsCode, il suffit de rentrer la configuration suivante :

.. sourcecode:: json

    {
        "python.formatting.provider": "black",
        "editor.formatOnSave": true
    }

Sublime Text
~~~~~~~~~~~~

Il est tout d'abord nécessaire d'installer ce plugin : https://packagecontrol.io/packages/sublack.

Il suffit ensuite d'ajouter dans les settings du projet (ou directement dans les settings globales) :

.. sourcecode:: json

    {
        "sublack.black_on_save": true
    }

Si vous utilisez le plugin `anaconda <http://damnwidget.github.io/anaconda/>`__, pensez à modifier les paramètres du linter pep8 pour éviter de recevoir des warnings dans le formatage de black comme ceci :

.. sourcecode:: json

    {
        "pep8_ignore": [
          "E203",
          "E266",
          "E501",
          "W503"
        ]
    }
