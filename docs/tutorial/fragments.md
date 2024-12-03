Pour utiliser HTMX, on a besoin de renvoyer des fragments depuis le backend.
Le truc, c'est que tout est optimisé pour utiliser `base.jinja` qui est assez gros.

Dans beaucoup de scénario, on veut pouvoir renvoyer soit la vue complète, soit
juste le fragment. En particulier quand on utilise l'attribut `hx-history` de htmx.

Pour remédier à cela, il existe le mixin [AllowFragment][core.views.AllowFragment].

Une fois ajouté à une vue Django, il ajoute le boolean `is_fragment` dans les
templates jinja. Sa valeur est `True` uniquement si HTMX envoie la requête.
Il est ensuite très simple de faire un if/else pour hériter de
`core/base_fragment.jinja` au lieu de `core/base.jinja` dans cette situation.

Exemple d'utilisation d'une vue avec fragment:

```python
from django.views.generic import TemplateView
from core.views import AllowFragment

class FragmentView(AllowFragment, TemplateView):
	template_name = "my_template.jinja"
```

Exemple de template (`my_template.jinja`)
```jinja
{% if is_fragment %}
  {% extends "core/base_fragment.jinja" %}
{% else %}
  {% extends "core/base.jinja" %}
{% endif %}


{% block title %}
  {% trans %}My view with a fragment{% endtrans %}
{% endblock %}

{% block content %}
  <h3>{% trans %}This will be a fragment when is_fragment is True{% endtrans %}
{% endblock %}
```
