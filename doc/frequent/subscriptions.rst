.. _add_subscription:

Ajouter une nouvelle cotisation
===============================

Il arrive régulièrement que le type de cotisation proposé varie en prix et en durée au cours des années. Le projet étant pensé pour être utilisé par d'autres associations dans la mesure du possible, ces cotisations sont configurables directement dans les paramètres du projet.

Comprendre la configuration
---------------------------

Pour modifier les cotisations disponibles, tout se gère dans la configuration avec la variable *SITH_SUBSCRIPTIONS*. Dans cet exemple, nous allons ajouter une nouvelle cotisation d'un mois.

.. code-block:: python

    from django.utils.translation import gettext_lazy as _

    SITH_SUBSCRIPTIONS = {
        # Voici un échantillon de la véritable configuration à l'heure de l'écriture.
        # Celle-ci est donnée à titre d'exemple pour mieux comprendre comment cela fonctionne.
        "un-semestre": {"name": _("One semester"), "price": 15, "duration": 1},
        "deux-semestres": {"name": _("Two semesters"), "price": 28, "duration": 2},
        "cursus-tronc-commun": {
            "name": _("Common core cursus"),
            "price": 45,
            "duration": 4,
        },
        "cursus-branche": {"name": _("Branch cursus"), "price": 45, "duration": 6},
        "cursus-alternant": {"name": _("Alternating cursus"), "price": 30, "duration": 6},
        "membre-honoraire": {"name": _("Honorary member"), "price": 0, "duration": 666},
        "un-jour": {"name": _("One day"), "price": 0, "duration": 0.00555333},

        # On rajoute ici notre cotisation
        # Elle se nomme "Un mois"
        # Coûte 6€
        # Dure 1 mois (on résonne en semestre, ici c'est 1/6 de semestre)
        "un-mois": {"name": _("One month"), "price": 6, "duration": 0.166}
    }

Créer une migration
-------------------

La modification de ce paramètre est étroitement lié à la génération de la base de données. Cette variable est utilisé dans l'objet *Subscription* pour générer les *subscription_type*. Le modifier requiers de générer une migration de basse de données.

.. code-block:: bash

    ./manage.py makemigrations subscription

.. note::

    N'oubliez pas d'appliquer black sur le fichier de migration généré.

Rajouter la traduction pour la cotisation
-----------------------------------------

Comme on peut l'observer, la cotisation a besoin d'un nom qui est internationalisé. Il est donc nécessaire de le traduire en français. Pour rajouter notre traduction de *"One month"* il faut se référer à cette partie de la documentation : :ref:`translations`.
