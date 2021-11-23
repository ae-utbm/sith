Générer l'environnement avec populate
=====================================

Lors de l'installation du site en local (via la commande `setup`), la commande **populate** est appelée.

Cette commande génère entièrement la base de données de développement. Elle se situe dans `core/management/commands/populate.py`.

Utilisations :

.. code-block:: shell

    ./manage.py setup # Génère la base de test
    ./manage.py setup --prod # Ne génère que le schéma de base et les données strictement nécessaires au fonctionnement

Les données générées du site dev
================================

Par défaut, la base de données du site de prod contient des données nécessaires au fonctionnement du site comme les groupes (voir :ref:`groups-list`), un utilisateur root, les clubs de base et quelques autres instances indispensables. En plus de ces données par défaut, la base de données du site de dev contient des données de test (*fixtures*) pour remplir le site et le rendre exploitable. 

**Voici les clubs générés pour le site de dev :**

    * AE

        - Bibo'UT
        - Carte AE
        - Guy'UT

            + Woenzel'UT

        - Troll Penché

    * BdF
    * Laverie

**Voici utilisateurs générés pour le site de dev :**

    Le mot de passe de tous les utilisateurs est **plop**.

    * **root** -> Dans le groupe Root et cotisant
    * **skia** -> responsable info AE et cotisant, barmen MDE
    * **public** -> utilisateur non cotisant et sans groupe
    * **subscriber** -> utilisateur cotisant et sans groupe
    * **old_subscriber** -> utilisateur anciennement cotisant et sans groupe
    * **counter** -> administrateur comptoir
    * **comptable** -> administrateur comptabilité
    * **guy** -> utilisateur non cotisant et sans groupe
    * **rbatsbak** -> utilisateur non cotisant et sans groupe
    * **sli** -> cotisant avec carte étudiante attachée au compte
    * **krophil** -> cotisant avec des plein d'écocups, barmen foyer
    * **comunity** -> administrateur communication
    * **tutu** -> administrateur pédagogie

Ajouter des fixtures
====================
.. role:: python(code)
    :language: python

Les fixtures sont contenus dans *core/management/commands/populate.py* après la ligne 205 : :python:`if not options["prod"]:`.

Pour ajouter une fixtures, il faut :

* importer la classe à instancier en début de fichier 
* créer un objet avec les attributs nécessaires en fin de fichier
* enregistrer l'objet dans la base de données

.. code-block:: python

    # Exemple pour ajouter un utilisateur

    # Importation de la classe
    import core.models import User

    # [...]
    
    # Création de l'objet
    jesus = User(
        username="jc",
        last_name="Jesus",
        first_name="Christ",
        email="son@god.cloud",
        date_of_birth="2020-24-12",
        is_superuser=False,
        is_staff=True,
    )
    jesus.set_password("plop")
    # Enregistrement dans la base de donnée
    jesus.save()