Le système de groupes
=====================

Il existe deux systèmes de groupes sur le site AE. L'un se base sur l'utilisation de groupes enregistrés en base de données pendant le développement, c'est le système de groupes réels. L'autre est plus dynamique et comprend tous les groupes générés pendant l'exécution et l'utilisation du programme. Cela correspond généralement aux groupes liés aux clubs. Ce sont les méta groupes.

La définition d'un groupe
--------------------------

Comme on peut l'observer, il existe une entrée de groupes dans la base de données. Cette classe implémente à la fois les groupes réels et les méta groupes.

Ce qui différencie ces deux types de groupes ce sont leur utilisation et leur manière d'être générés. La distinction est faite au travers de la propriété `is_meta`.

.. autoclass:: core.models.Group
    :members:

Les groupes réels
-----------------

Pour simplifier l'utilisation de ces deux types de groupe, il a été crée une classe proxy (c'est à dire qu'elle ne correspond pas à une vraie table en base de donnée) qui encapsule leur utilisation. RealGroup peut être utilisé pour créer des groupes réels dans le code et pour faire une recherche sur ceux-ci (dans le cadre d'une vérification de permissions par exemple).

.. autoclass:: core.models.RealGroup
    :members:

.. note::

    N'oubliez pas de créer une variable dans les settings contenant le numéro du groupe pour facilement l'utiliser dans le code plus tard. Ces variables sont du type `SITH_GROUP_GROUPE_NAME_ID`.

Les méta groupes
----------------

Les méta groupes, comme expliqués précédemment, sont utilisés dans les contextes où il est nécessaire de créer un groupe *on runtime*. C'est principalement utilisé au travers des clubs qui créent automatiquement à leur création deux groupes :  et .

* club-bureau : contient tous les membres d'un club **au dessus** du grade défini dans settings.SITH_MAXIMUM_FREE_ROLE.
* club-membres : contient tous les membres d'un club **en dessous** du grade défini dans settings.SITH_MAXIMUM_FREE_ROLE.

.. autoclass:: core.models.MetaGroup
    :members:


.. _groups-list:

La liste des groupes réels
--------------------------

Les groupes réels existant par défaut dans le site sont les suivants :

Groupes gérés automatiquement par le site :

* **Public** -> tous les utilisateurs du site
* **Subscribers** -> tous les cotisants du site
* **Old subscribers** -> tous les anciens cotisants

Groupes gérés par les administrateurs (à appliquer à la main sur un utilisateur) :

* **Root** -> administrateur global du site
* **Accounting admin** -> les administrateurs de la comptabilité
* **Communication admin** -> les administrateurs de la communication
* **Counter admin** -> les administrateurs des comptoirs (foyer et autre)
* **SAS admin** -> les administrateurs du SAS
* **Forum admin** -> les administrateurs du forum
* **Pedagogy admin** -> les administrateurs de la pédagogie (guide des UVs)
* **Banned from buying alcohol** -> les utilisateurs interdits de vente d'alcool (non mineurs)
* **Banned from counters** -> les utilisateurs interdits d'utilisation des comptoirs
* **Banned to subscribe** -> les utilisateurs interdits de cotisation
