Générer l'environnement avec populate
=====================================

Lors de l'installation du site en local (via la commande `setup`), la commande **populate** est appelée.

Cette commande génère entièrement la base de donnée de développement. Elle se situe dans `core/management/commands/populate.py`.

Utilisations :

.. code-block:: shell

    ./manage.py setup # Génère la base de test
    ./manage.py setup --prod # Ne génère que le schéma de base et les données strictement nécessaires au fonctionnement

Les groupes du site de dev
==========================

La liste exhaustive des groupes est disponible ici : :ref:`groups-list`.

Les clubs du site de dev
========================

Voici la liste des groupes avec leur arborescence d'appartenance. 

* AE

    - Bibo'UT
    - Carte AE
    - Guy'UT

        + Woenzel'UT

    - Troll Penché

* BdF
* Laverie

Les utilisateurs du site de dev
===============================

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