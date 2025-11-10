## Qu'est-ce qu'un fragment

Une application web django traditionnelle suit en général
le schéma suivant : 

1. l'utilisateur envoie une requête au serveur
2. le serveur renvoie une page HTML,
   qui contient en général des liens et/ou des formulaires
3. lorsque l'utilisateur clique sur un lien ou valide
   un formulaire, on retourne à l'étape 1

C'est un processus qui marche, mais qui est lourd :
générer une page entière demande du travail au serveur
et effectuer le rendu de cette page en demande également
beaucoup au client.
Or, des temps de chargement plus longs et des
rechargements complets de page peuvent nuire
à l'expérience utilisateur, en particulier
lorsqu'ils interviennent lors d'opérations simples.

Pour éviter ce genre de rechargement complet,
on peut utiliser AlpineJS pour rendre la page
interactive et effectuer des appels à l'API.
Cette technique fonctionne particulièrement bien
lorsqu'on veut afficher des objets ou des listes
d'objets de manière dynamique.

En revanche, elle est moins efficace pour certaines
opérations, telles que la validation de formulaire.
En effet, valider un formulaire demande beaucoup
de travail de nettoyage des données et d'affichage
des messages d'erreur appropriés.
Or, tout ce travail existe déjà dans Django.

On veut donc, dans ces cas-là, ne pas demander
toute une page HTML au serveur, mais uniquement
une toute petite partie, que l'on utilisera
pour remplacer la partie qui correspond sur la page actuelle.
Ce sont des fragments.


## HTMX

Toutes les fonctionnalités d'interaction avec les
fragments, côté client, s'appuient sur la librairie htmx.

L'usage qui en est fait est en général assez simple
et ressemblera souvent à ça :

```html+jinja
<form
  hx-trigger="submit"  {# Lorsque le formulaire est validé... #}
  hx-post="{{ url("foo:bar") }}"  {# ...envoie une requête POST vers l'url donnée... #}
  hx-swap="outerHTML" {# ...et remplace tout l'html du formulaire par le contenu de la réponse HTTP #}
>
  {% csrf_token %}
  {{ form }}
  <input type="submit" value="{% trans %}Go{% endtrans %}"/>
</form>
```

C'est la majorité de ce que vous avez besoin de savoir
pour utiliser HTMX sur le site.

Bien entendu, ce n'est pas tout, il y a d'autres
options et certaines subtilités, mais pour ça,
consultez [la doc officielle d'HTMX](https://htmx.org/docs/).

## La surcouche du site

Pour faciliter et standardiser l'intégration d'HTMX
dans la base de code du site AE,
nous avons créé certains mixins à utiliser
dans les vues basées sur des classes.

### [AllowFragment][core.views.mixins.AllowFragment]

`AllowFragment` est extrêmement simple dans son
concept : il met à disposition la variable `is_fragment`,
qui permet de savoir si la vue est appelée par HTMX,
ou si elle provient d'un autre contexte.

Grâce à ça, on peut écrire des vues qui 
fonctionnent dans les deux contextes.

Par exemple, supposons que nous avons
une `UpdateView` très simple, contenant
uniquement un formulaire.
On peut écrire la vue et le template de la manière
suivante :

=== "`views.py`"

    ```python
    from django.views.generic import UpdateView

    from core.views import AllowFragment


    class FooUpdateView(AllowFragment, UpdateView):
        model = Foo
        fields = ["foo", "bar"]
        pk_url_kwarg = "foo_id"
        template_name = "app/foo.jinja"
    ```

=== "`app/foo.jinja`"

    ```html+jinja
    {% if is_fragment %}
      {% extends "core/base_fragment.jinja" %}
    {% else %}
      {% extends "core/base.jinja" %}
    {% endif %}

    {% block content %}
      <form hx-trigger="submit" hx-swap="outerHTML">
        {% csrf_token %}
        {{ form }}
        <input type="submit" value="{% trans %}Go{% endtrans %}"/>
      </form>
    {% endblock %}
    ```

Lors du chargement initial de la page, le template
entier sera rendu, mais lors de la soumission du formulaire,
seul le fragment html de ce dernier sera changé.

### [FragmentMixin][core.views.mixins.FragmentMixin]

Il arrive des situations où le résultat que l'on
veut accomplir est plus complexe.
Dans ces situations, pouvoir décomposer une vue
en plusieurs vues de fragment permet de ne plus 
raisonner en termes de condition, mais en termes
de composition : on n'a pas un seul template
qui peut changer selon les situations, on a plusieurs
templates que l'on injecte dans un template principal.

Supposons, par exemple, que nous n'avons plus un,
mais deux formulaires à afficher sur la page.
Dans ce cas, nous pouvons créer deux templates,
qui seront alors injectés.

=== "`urls.py`"

    ```python
    from django.urls import path
   
    from app import views

    urlpatterns = [
        path("", FooCompositeView.as_view(), name="main"),
        path("create/", FooUpdateFragment.as_view(), name="update_foo"),
        path("update/", FooCreateFragment.as_view(), name="create_foo"),
    ]
    ```

=== "`view.py`"

    ```python
    from django.views.generic import CreateView, UpdateView, TemplateView
    from core.views.mixins import FragmentMixin
    
    
    class FooCreateFragment(FragmentMixin, CreateView):
        model = Foo
        fields = ["foo", "bar"]
        template_name = "app/fragments/create_foo.jinja"


    class FooUpdateFragment(FragmentMixin, UpdateView):
        model = Foo
        fields = ["foo", "bar"]
        pk_url_kwarg = "foo_id"
        template_name = "app/fragments/update_foo.jinja"


    class FooCompositeFormView(TemplateView):
        template_name = "app/foo.jinja"

        def get_context_data(**kwargs):
            return super().get_context_data(**kwargs) | {
                "create_fragment": FooCreateFragment.as_fragment()(),
                "update_fragment": FooUpdateFragment.as_fragment()(foo_id=1)
            }
    ```
 
=== "`app/fragment/create_foo.jinja`"
   
    ```html+jinja
    <form 
      hx-trigger="submit" 
      hx-post="{{ url("app:create_foo") }}" 
      hx-swap="outerHTML"
    >
      {% csrf_token %}
      {{ form }}
      <input type="submit" value="{% trans %}Create{% endtrans %}"/>
    </form>
    ```

=== "`app/fragment/update_foo.jinja`"

    ```html+jinja
    <form 
      hx-trigger="submit" 
      hx-post="{{ url("app:update_foo") }}" 
      hx-swap="outerHTML"
    >
      {% csrf_token %}
      {{ form }}
      <input type="submit" value="{% trans %}Update{% endtrans %}"/>
    </form>
    ```

=== "`app/foo.jinja`"

    ```html+jinja
    {% extends "core/base.html" %}
    
    {% block content %}
      <h2>{% trans %}Update current foo{% endtrans %}</h2> 
      {{ update_fragment }}
    
      <h2>{% trans %}Create new foo{% endtrans %}</h2> 
      {{ create_fragment }}
    {% endblock %}
    ```

Le résultat consistera en l'affichage d'une page
contenant deux formulaires.
Le rendu des fragments n'est pas effectué
par `FooCompositeView`, mais par les vues
des fragments elles-mêmes, en sautant
les méthodes `dispatch` et `get`/`post` de ces dernières.
À chaque validation de formulaire, la requête
sera envoyée à la vue responsable du fragment,
qui se comportera alors comme une vue normale.

#### La méthode `as_fragment`

Il est à noter que l'instanciation d'un fragment
se fait en deux étapes :

- on commence par instancier la vue en tant que renderer.
- on appelle le renderer en lui-même

Ce qui donne la syntaxe `Fragment.as_fragment()()`.

Cette conception est une manière de se rapprocher
le plus possible de l'interface déjà existante
pour la méthode `as_view` des vues.
La méthode `as_fragment` prend en argument les mêmes
paramètres que `as_view`.

Par exemple, supposons que nous voulons rajouter
des variables de contexte lors du rendu du fragment.
On peut écrire ça ainsi :

```python
fragment = Fragment.as_fragment(extra_context={"foo": "bar"})()
```

#### Personnaliser le rendu

En plus de la personnalisation permise par
`as_fragment`, on peut surcharger la méthode
`render_fragment` pour accomplir des actions
spécifiques, et ce uniquement lorsqu'on effectue
le rendu du fragment.

Supposons qu'on veuille manipuler un entier
dans la vue et que, lorsqu'on est en train
de faire le rendu du template, on veuille augmenter
la valeur de cet entier (c'est juste pour l'exemple).
On peut écrire ça ainsi :

```python
from django.views.generic import CreateView
from core.views.mixins import FragmentMixin


class FooCreateFragment(FragmentMixin, CreateView):
    model = Foo
    fields = ["foo", "bar"]
    template_name = "app/fragments/create_foo.jinja"

    def render_fragment(self, request, **kwargs):
        if "foo" in kwargs:
           kwargs["foo"] += 2
        return super().render_fragment(request, **kwargs)
```

Et on effectuera le rendu du fragment de la manière suivante :

```python
FooCreateFragment.as_fragment()(foo=4)
```

### [UseFragmentsMixin][core.views.mixins.UseFragmentsMixin]

Lorsqu'on a plusieurs fragments, il est parfois
plus aisé des les aggréger au sein de la vue
principale en utilisant `UseFragmentsMixin`.

Elle permet de marquer de manière plus explicite
la séparation entre les fragments et le reste du contexte.

Reprenons `FooUpdateFragment` et la version modifiée
de `FooCreateFragment`.
`FooCompositeView` peut être réécrite ainsi :

```python
from django.views.generic import TemplateView
from core.views.mixins import UseFragmentsMixin


class FooCompositeFormView(UseFragmentsMixin, TemplateView):
    fragments = {
        "create_fragment": FooCreateFragment,
        "update_fragment": FooUpdateFragment
    }
    fragment_data = {
       "update_fragment": {"foo": 4}
    }
    template_name = "app/foo.jinja"
```

Le résultat sera alors strictement le même.

Pour personnaliser le rendu de tous les fragments,
on peut également surcharger la méthode
`get_fragment_context_data`.
Cette méthode remplit les mêmes objectifs
que `get_context_data`, mais uniquement pour les fragments.
Il s'agit simplement d'un utilitaire pour séparer les responsabilités.

```python
from django.views.generic import TemplateView
from core.views.mixins import UseFragmentsMixin


class FooCompositeFormView(UseFragmentsMixin, TemplateView):
    fragments = {
        "create_fragment": FooCreateFragment
    }
    template_name = "app/foo.jinja"

    def get_fragment_context_data(self):
        # let's render the update fragment here
        # instead of using the class variables
        return super().get_fragment_context_data() | {
            "create_fragment": FooUpdateFragment.as_fragment()(foo=4)
        }
```


