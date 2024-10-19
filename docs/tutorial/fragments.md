Pour utiliser HTMX, on a besoin de renvoyer des fragments depuis le backend.
Le truc, c'est que tout est optimisé pour utiliser `base.jinja` qui est assez gros.

Dans beaucoup de scénario, on veut pouvoir renvoyer soit la vue complète, soit
juste le fragment. En particulier quand on utilise l'attribut `hx-history` de htmx.

Pour remédier à cela, il existe le mixin [AllowFragment][core.views.AllowFragment].

Une fois ajouté à une vue Django, il ajoute le boolean `is_fragment` dans les
templates jinja. Sa valeur est `True` uniquement si HTMX envoi la requette.
Il est ensuite très simple de faire un if/else pour hériter de
`core/base_fragment.jinja` au lieu de `core/base.jinja` dans cette situation.