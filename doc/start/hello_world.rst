Créer une nouvelle application Hello World
==========================================

L'objectif de ce petit tutoriel est de prendre rapidement en main les vues, les urls et les modèles de Django. On créera une application nommée *hello* qui fournira une page affichant "Hello World", une autre page qui affichera en plus un numéro qui sera récupéré depuis l'URL ainsi qu'une page affichant un élément récupéré de la base de données, le tout au milieu d'une page typique du Sith AE.

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
        template_name = "hello/hello.jinja" # On indique quel template utiliser

On vas ensuite créer le template.

.. code-block:: html+jinja

    {# hello/templates/hello/hello.jinja #}

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
        template_name = "hello/hello.jinja"

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

    {# hello/templates/hello/hello.jinja #}
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

.. note::

    Il est tout à fait possible d'utiliser les arguments GET passés dans l'URL. Dans ce cas, il n'est pas obligatoire de modifier l'URL et il est possible de récupérer l'argument dans le dictionnaire `request.GET`.

À l'assaut des modèles
----------------------

Pour cette dernière partie, nous allons ajouter une entrée dans la base de donnée et l'afficher dans un template. Nous allons ainsi créer un modèle nommé *Article* qui contiendra une entrée de texte pour le titre et une autre pour le contenu.

Commençons par le modèle en lui même.

.. code-block:: python

    # hello/models.py
    from django.db import models


    class Article(models.Model):

        title = models.CharField("titre", max_length=100)
        content = models.TextField("contenu")

Continuons avec une vue qui sera en charge d'afficher l'ensemble des articles présent dans la base.

.. code-block:: python

    # hello/views.py

    from django.views.generic import ListView

    from hello.models import Article

    ...

    # On hérite de ListView pour avoir plusieurs objets
    class ArticlesListView(ListView):

        model = Article # On base la vue sur le modèle Article
        template_name = "hello/articles.jinja"

On n'oublie pas l'URL.

.. code-block:: python

    from hello.views import HelloView, ArticlesListView

    urlpatterns = [
        ...
        url(r"^articles$", ArticlesListView.as_view(), name="articles_list")
    ]

Et enfin le template.

.. code-block:: html+jinja

    {# hello/templates/hello/articles.jinja #}
    {% extends "core/base.jinja" %}

    {% block title %}
        Hello World Articles
    {% endblock title %}

    {% block content %}
        {# Par défaut une liste d'objets venant de ListView s'appelle object_list #}
        {% for article in object_list %}
            <h2>{{ article.title }}</h2>
            <p>{{ article.content }}</p>
        {% endfor %}
    {% endblock content %}

Maintenant que toute la logique de récupération et d'affichage est terminée, la page est accessible à l'adresse https://localhost:8000/hello/articles.

Mais, j'ai une erreur ! Il se passe quoi ?! Et bien c'est simple, nous avons crée le modèle mais il n'existe pas dans la base de données. Il est dans un premier temps important de créer un fichier de migrations qui contiens des instructions pour la génération de celle-ci. Ce sont les fichiers qui sont enregistrés dans le dossier migration. Pour les générer à partir des classes de modèles qu'on viens de manipuler il suffit d'une seule commande.

.. code-block:: bash

    ./manage.py makemigrations

Un fichier *hello/migrations/0001_initial.py* se crée automatiquement, vous pouvez même aller le voir.

.. note::

    Il est tout à fait possible de modifier à la main les fichiers de migrations. C'est très intéressant si par exemple il faut appliquer des modifications sur les données d'un modèle existant après cette migration mais c'est bien au delà du sujet de ce tutoriel. Référez vous à la documentation pour ce genre de choses.

J'ai toujours une erreur ! Mais oui, c'est pas fini, faut pas aller trop vite. Maintenant il faut appliquer les modifications à la base de données.

.. code-block:: bash

    ./manage.py migrate

Et voilà, là il n'y a plus d'erreur. Tout fonctionne et on a une superbe page vide puisque aucun contenu pour cette table n'est dans la base. Nous allons en rajouter. Pour cela nous allons utiliser le fichier *core/management/commands/populate.py* qui contiens la commande qui initialise les données de la base de données de test. C'est un fichier très important qu'on viendra à modifier assez souvent. Nous allons y ajouter quelques articles.

.. code-block:: python

    # core/management/commands/populate.py
    from hello.models import Article

    ...

    class Command(BaseCommand):

        ...

        def handle(self, *args, **options):

            ...

            Article(title="First hello", content="Bonjour tout le monde").save()
            Article(title="Tutorial", content="C'était un super tutoriel").save()


On regénère enfin les données de test en lançant la commande que l'on viens de modifier.

.. code-block:: bash

    ./manage.py setup

On reviens sur https://localhost:8000/hello/articles et cette fois-ci nos deux articles apparaissent correctement.