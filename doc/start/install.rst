Installer le projet
===================

Dépendances du système
----------------------

Certaines dépendances sont nécessaires niveau système :

* virtualenv
* libmysqlclient
* libssl
* libjpeg
* python3-xapian
* zlib1g-dev
* python3
* gettext
* graphviz
* mysql-client (pour migrer de l'ancien site)

Sur Ubuntu
~~~~~~~~~~

.. sourcecode:: bash

    sudo apt install libmysqlclient-dev libssl-dev libjpeg-dev zlib1g-dev python3-dev libffi-dev python3-dev libgraphviz-dev pkg-config python3-xapian gettext git
    sudo pip3 install virtualenv

Sur MacOS
~~~~~~~~~

Pour installer les dépendances, il est fortement recommandé d'installer le gestionnaire de paquets `homebrew <https://brew.sh/index_fr>`_.

.. sourcecode:: bash

    brew install git python xapian graphviz

    # Si vous aviez une version de python ne venant pas de homebrew
    brew link --overwrite python


    # Pour bien configurer gettext
    brew link gettext # (suivez bien les instructions supplémentaires affichées)

    # Pour installer virtualenv
    pip3 install virtualenv

.. note::

    Si vous rencontrez des erreurs lors de votre configuration, n'hésitez pas à vérifier l'état de votre installation homebrew avec :code:`brew doctor`

Installer le projet
-------------------

.. sourcecode:: bash

    git clone https://ae-dev.utbm.fr/ae/Sith.git
    cd Sith

    # Prépare et active l'environnement du projet
    virtualenv --system-site-packages --python=python3 env
    source env/bin/activate

    # Installe les dépendances du projet
    pip install -r requirements.txt

    # Si vous avez des problèmes avec graphiviz
    pip install pygraphviz --install-option="--include-path=/usr/include/graphviz" --install-option="--library-path=/usr/lib/graphviz/"

    # Prépare la base de donnée
    ./manage.py setup

    # Installe les traductions
    ./manage compilemessages

.. note::

    Pour éviter d'avoir à utiliser la commande source sur le virtualenv systématiquement, il est possible de consulter :ref:`direnv`.

Configuration pour le développement
-----------------------------------

Lorsqu'on souhaite développer pour le site, il est nécessaire de passer le logiciel en mode debug dans les settings_custom. Il est aussi conseillé de définir l'URL du site sur localhost. Voici un script rapide pour le faire.

.. sourcecode:: bash

    echo "DEBUG=True" > sith/settings_custom.py
    echo 'SITH_URL = "localhost:8000"' >> sith/settings_custom.py

Démarrer le serveur de développement
------------------------------------

Il faut toujours avoir préalablement activé l'environnement virtuel comme fait plus haut et se placer à la racine du projet. Il suffit ensuite d'utiliser cette commande :

.. sourcecode:: bash

    ./manage.py runserver

.. note::

    Le serveur est alors accessible à l'adresse http://localhost:8000.

Générer la documentation
------------------------

La documentation est automatiquement mise en ligne sur readthedocs à chaque envoi de code sur GitLab.

Pour l'utiliser en local ou globalement pour la modifier, il existe une commande du site qui génère la documentation et lance un serveur la rendant accessible à l'adresse http://localhost:8080.

.. sourcecode:: bash

    ./manage.py documentation

Lancer les tests
----------------

Pour lancer les tests il suffit d'utiliser la commande intégrée à django.

.. code-block:: bash

    # Lancer tous les tests
    ./manage.py test

    # Lancer les tests de l'application core
    ./manage.py test core

    # Lancer les tests de la classe UserRegistrationTest de core
    ./manage.py test core.tests.UserRegistrationTest

    # Lancer une méthode en particulier de cette même classe
    ./manage.py test core.tests.UserRegistrationTest.test_register_user_form_ok
