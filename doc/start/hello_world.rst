Créer une nouvelle application Hello World
==========================================

L'objectif de ce petit tutoriel est de manier les vues et les urls de Django simplement. On créera une application nommée *hello* qui fournira une page affichant "Hello World" ainsi qu'une autre page qui affichera en plus un numéro qui sera récupéré depuis l'URL, le tout au milieu d'une page typique du Sith AE.

Créer l'application
-------------------

La première étape est de crée l'application. Cela se fait très simplement avec les outils fournis par le framework.

.. code-block:: bash

    ./manage.py startapp hello

Il faut ensuite activer l'application dans les paramètres du projet en l'ajoutant dans la liste des applications installées.

.. code-block:: python

    # sith/settings.py

    # ...

    INSTALLED_APPS = (
        ...
        "hello",
    )

Enfin, on vas inclure les URLs de cette application dans le projet sous le préfixe */hello/*.

.. code-block:: python

    # sith/urls.py
    urlpatterns = [
        ...
        url(r"^hello/", include("hello.urls", namespace="hello", app_name="hello")),
    ]

Un Hello World simple
---------------------

Dans un premier temps, nous allons créer une vue qui vas charger un template en utilisant le système de vues basées sur les classes de Django.

.. code-block:: python

    # hello/views.py

    from django.views.generic import TemplateView

    # Toute la logique pour servir la vue et parser le template
    # est directement héritée de TemplateView
    class HelloView(TemplateView):
        template_name = "hello.jinja" # On indique quel template utiliser

On vas ensuite créer le template.

.. code-block:: html+jinja

    {# hello/templates/hello.jinja #}

    {# On étend le template de base du Sith #}
    {% extends "core/base.jinja" %}

    {# On remplis la partie titre du template étendu #}
    {# Il s'agit du titre qui sera affiché dans l'onglet du navigateur #}
    {% block title %}
    Hello World
    {% endblock title %}

    {# On remplis le contenu de la page #}
    {% block content %}
    <p>Hello World !</p>
    {% endblock content %}

Enfin, on crée l'URL. On veut pouvoir appeler la page depuis https://localhost:8000/hello, le préfixe indiqué précédemment suffit donc.

.. code-block:: python

    # hello/urls.py
    from django.conf.urls import url
    from hello.views import HelloView

    urlpatterns = [
       # Le préfixe étant retiré lors du passage du routeur d'URL
       # dans le fichier d'URL racine du projet, l'URL à matcher ici est donc vide
       url(r"^$", HelloView.as_view(), name="hello"),
    ]

Et voilà, c'est fini, il ne reste plus qu'à lancer le serveur et à se rendre sur la page.

Manipuler les arguments d'URL
-----------------------------

Dans cette partie, on cherche à détecter les numéros passés dans l'URL pour les passer dans le template. On commence par ajouter cet URL modifiée.

.. code-block:: python

    # hello/urls.py
    from django.conf.urls import url
    from hello.views import HelloView

    urlpatterns = [
       url(r"^$", HelloView.as_view(), name="hello"),
       # On utilise un regex pour matcher un numéro
       url(r"^(?P<hello_id>[0-9]+)$", HelloView.as_view(), name="hello"),
    ]

Cette deuxième URL vas donc appeler la classe crée tout à l'heure en lui passant une variable *hello_id* dans ses *kwargs*, nous allons la récupérer et la passer dans le contexte du template en allant modifier la vue.

.. code-block:: python

    # hello/views.py
    from django.views.generic import TemplateView

    class HelloView(TemplateView):
        template_name = "hello.jinja"

        # C'est la méthode appelée juste avant de définir le type de requête effectué
        def dispatch(self, request, *args, **kwargs):

            # On récupère l'ID et on le met en attribut
            self.hello_id = kwargs.pop("hello_id", None)

            # On reprend le déroulement normal en appelant la méthode héritée
            return super(HelloView, self).dispatch(request, *args, **kwargs)

        # Cette méthode renvoie les variables qui seront dans le contexte du template
        def get_context_data(self, **kwargs):

            # On récupère ce qui était sensé être par défaut dans le contexte
            kwargs = super(HelloView, self).get_context_data(**kwargs)

            # On ajoute notre ID
            kwargs["hello_id"] = self.hello_id

            # On renvoie le contexte
            return kwargs

Enfin, on modifie le template en rajoutant une petite condition sur la présence ou non de cet ID pour qu'il s'affiche.

.. code-block:: html+jinja

    {# hello/templates/hello.jinja #}
    {% extends "core/base.jinja" %}

    {% block title %}
    Hello World
    {% endblock title %}

    {% block content %}
    <p>
        Hello World !
        {% if hello_id -%}
        {{ hello_id }}
        {%- endif -%}
    </p>
    {% endblock content %}
