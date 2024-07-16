## Ajouter une nouvelle cotisation

Il peut arriver que le type de cotisation
proposé varie en prix et en durée.
Ces paramètres sont configurables directement dans les paramètres du projet.

Pour modifier les cotisations disponibles, 
tout se gère dans la configuration avec la variable `SITH_SUBSCRIPTIONS`.

Par exemple, si nous voulons ajouter une nouvelle cotisation d'un mois,
voici ce que nous ajouterons :

```python title="settings.py"
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
    # Dure 1 mois (on raisonne en semestre, ici, c'est 1/6 de semestre)
    "un-mois": {"name": _("One month"), "price": 6, "duration": 0.166}
}
```

Une fois ceci fait, il faut créer une nouvelle migration :

```bash
python ./manage.py makemigrations subscription
python ./manage.py migrate
```

N'oubliez pas non plus les traductions (cf. [ici](./translation.md))
