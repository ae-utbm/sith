Installer le projet
===================

Dépendances du système
----------------------

Certaines dépendances sont nécessaires niveau système :

* poetry
* libssl
* libjpeg
* zlib1g-dev
* python
* gettext
* graphviz

Sur Windows
~~~~~~~~~~~

Chers utilisateurs de Windows, quel que soit votre amour de Windows,
de Bill Gates et des bloatwares, je suis désolé
de vous annoncer que, certaines dépendances étant uniquement disponibles sur des sytèmes UNIX,
il n'est pas possible développer le site sur Windows.

Heureusement, il existe une alternative qui ne requiert pas de désinstaller votre
OS ni de mettre un dual boot sur votre ordinateur : :code:`WSL`.

- **Prérequis:** vous devez être sur Windows 10 version 2004 ou ultérieure (build 19041 & versions ultérieures) ou Windows 11.
- **Plus d'info:** `docs.microsoft.com <https://docs.microsoft.com/fr-fr/windows/wsl/install>`_

.. sourcecode:: bash

    # dans un shell Windows
    wsl --install

    # afficher la liste des distribution disponible avec WSL
    wsl -l -o

    # installer WSL avec une distro (ubuntu conseillé)
    wsl --install -d <nom_distro>

.. note::

  Si vous rencontrez le code d'erreur ``0x80370102``, regardez les réponses de ce `post <https://askubuntu.com/questions/1264102/wsl-2-wont-run-ubuntu-error-0x80370102>`_.

Une fois :code:`WSL` installé, mettez à jour votre distro & installez les dépendances **(voir la partie installation sous Ubuntu)**.

.. note::

    Comme `git` ne fonctionne pas de la même manière entre Windows & Unix, il est nécessaire de cloner le repository depuis Windows.
    (cf: `stackoverflow.com <https://stackoverflow.com/questions/62245016/how-to-git-clone-in-wsl>`_)

Pour accéder au contenu d'un répertoire externe à :code:`WSL`, il suffit simplement d'utiliser la commande suivante:

.. sourcecode:: bash

  # oui c'est beau, simple et efficace
  cd /mnt/<la_lettre_du_disque>/vos/fichiers/comme/dhab

Une fois l'installation des dépendances terminée (juste en dessous), il vous suffira, pour commencer à dev, d'ouvrir votre plus bel IDE et d'avoir 2 consoles:
1 console :code:`WSL` pour lancer le projet & 1 console pour utiliser :code:`git`

.. note::

    A ce stade, si vous avez réussi votre installation de :code:`WSL` ou bien qu'il
    était déjà installé, vous pouvez effectuer la mise en place du projet en suivant
    les instructions pour Ubuntu.


Sur Ubuntu
~~~~~~~~~~

.. sourcecode:: bash

    # Sait-on jamais
    sudo apt update

    sudo apt install python-is-python3 # Permet d'utiliser python au lieu de python3, c'est optionnel

    sudo apt install build-essentials libssl-dev libjpeg-dev zlib1g-dev python-dev \
                     libffi-dev python-dev-is-python3 libgraphviz-dev pkg-config \
                     gettext git pipx

    pipx install poetry

.. note::

    Si vous avez réussi à exécuter les instructions ci-dessus sans trop de problèmes,
    vous pouvez passer à la partie :ref:`Finalise installation`

Sur MacOS
~~~~~~~~~

Pour installer les dépendances, il est fortement recommandé d'installer le gestionnaire de paquets `homebrew <https://brew.sh/index_fr>`_.  
Il est également nécessaire d'avoir installé xcode

.. sourcecode:: bash

    echo 'export PATH="$(brew --prefix graphviz)/bin:$PATH"' >> ~/.zshrc
    echo 'export CFLAGS="-isysroot /Library/Developer/CommandLineTools/SDKs/MacOSX.sdk -I $(brew --prefix graphviz)/include"' >> ~/.zshrc
    echo 'export LDFLAGS="-L /Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/lib -L $(brew --prefix graphviz)/lib"' >> ~/.zshrc

    brew install git python graphviz pipx
    pipx install poetry

    # Pour bien configurer gettext
    brew link gettext # (suivez bien les instructions supplémentaires affichées)

.. note::

    Si vous rencontrez des erreurs lors de votre configuration, n'hésitez pas à vérifier l'état de votre installation homebrew avec :code:`brew doctor`

.. note::

    Si vous avez réussi à exécuter les instructions ci-dessus sans trop de problèmes,
    vous pouvez passer à la partie :ref:`Finalise installation`

.. _Finalise installation:

Finaliser l'installation
------------------------

.. sourcecode:: bash

    # Les commandes git doivent se faire depuis le terminal de Windows si on utilise WSL !
    git clone https://github.com/ae-utbm/sith3.git
    cd sith3

    # Création de l'environnement et installation des dépendances
    poetry install

    # Activation de l'environnement virtuel
    poetry shell

    # Installe xapian
    python manage.py install_xapian

    # Prépare la base de données
    python manage.py setup

    # Installe les traductions
    python manage.py compilemessages

.. note::

    Pour éviter d'avoir à utiliser la commande poetry shell systématiquement, il est possible de consulter :ref:`direnv`.

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

    python manage.py runserver

.. note::

    Le serveur est alors accessible à l'adresse http://localhost:8000 ou bien http://127.0.0.1:8000/.

Générer la documentation
------------------------

La documentation est automatiquement mise en ligne sur readthedocs à chaque envoi de code sur GitHub.
Pour l'utiliser en local ou globalement pour la modifier, il existe une commande du site qui génère la documentation et lance un serveur la rendant accessible à l'adresse http://localhost:8080.
Cette commande génère la documentation à chacune de ses modifications, inutile de relancer le serveur à chaque fois.

.. note::

    Les dépendances pour la documentation sont optionnelles.
    Avant de commencer à travailler sur la doc, il faut donc les installer
    avec la commande :code:`poetry install -E docs`

.. sourcecode:: bash

    python manage.py documentation

    # Il est possible de spécifier un port et une adresse d'écoute différente
    python manage.py documentation adresse:port

Lancer les tests
----------------

Pour lancer les tests il suffit d'utiliser la commande intégrée à django.

.. code-block:: bash

    # Lancer tous les tests
    python manage.py test

    # Lancer les tests de l'application core
    python manage.py test core

    # Lancer les tests de la classe UserRegistrationTest de core
    python manage.py test core.tests.UserRegistrationTest

    # Lancer une méthode en particulier de cette même classe
    python manage.py test core.tests.UserRegistrationTest.test_register_user_form_ok

Vérifier les dépendances Javascript
-----------------------------------

Une commande a été écrite pour vérifier les éventuelles mises à jour à faire sur les librairies Javascript utilisées.
N'oubliez pas de mettre à jour à la fois le fichier de la librairie, mais également sa version dans `sith/settings.py`.

.. code-block:: bash

    # Vérifier les mises à jour
    python manage.py check_front
