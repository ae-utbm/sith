Installer le projet
===================

Dépendances du système
----------------------

Certaines dépendances sont nécessaires niveau système :

* virtualenv
* limysqlclient
* libssl
* libjpeg
* python3-xapian
* zlib1g-dev
* python3
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

	brew install git python xapian
	pip install virtualenv

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

	# Prépare la base de donnée
	./manage.py setup

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
