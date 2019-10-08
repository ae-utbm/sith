La gestion des droits
=====================

La gestion des droits dans l'association étant très complexe, le système de permissions intégré dans Django ne suffisait pas, il a donc fallu créer et intégrer le notre.

La gestion des permissions se fait directement sur un modèle, il existe trois niveaux de permission :

* Édition des propriétés de l'objet
* Édition de certaines valeurs l'objet
* Voir l'objet

Protéger un modèle
------------------

Lors de l'écriture d'un modèle, il est très simple de définir des permissions. Celle-ci peuvent être basées sur des groupes et/ou sur des fonctions personnalisées.

Nous allons présenter ici les deux techniques. Dans un premier temps nous allons protéger une classe Article par groupes.

.. code-block:: python

    from django.db import models
    from django.conf import settings
    from django.utils.translation import ugettext_lazy as _

    from core.views import *
    from core.models import User, Group

    # Utilisation de la protection par groupe
    class Article(models.Model):

        title = models.CharField(_("title"), max_length=100)
        content = models.TextField(_("content"))

        # Ne peut pas être une liste
        # Groupe possédant l'objet
        # Donne les droits d'édition des propriétés de l'objet
        owner_group = models.ForeignKey(
            Group, related_name="owned_articles", default=settings.SITH_GROUP_ROOT_ID
        )

        # Doit être une liste
        # Tous les groupes qui seront ajouté dans ce champ auront les droits d'édition de l'objet
        edit_group = models.ManyToManyField(
            edit_groups = models.ManyToManyField(
                Group,
                related_name="editable_articles",
                verbose_name=_("edit groups"),
                blank=True,
            )
        )

        # Doit être une liste
        # Tous les groupes qui seront ajouté dans ce champ auront les droits de vue de l'objet
        view_groups = models.ManyToManyField(
            Group,
            related_name="viewable_articles",
            verbose_name=_("view groups"),
            blank=True,
        )

Voici maintenant comment faire en définissant des fonctions personnalisées. Cette deuxième solution permet, dans le cas où la première n'est pas assez puissante, de créer des permissions complexes et fines. Attention à bien les rendre lisibles et de bien documenter.

.. code-block:: python

    from django.db import models
    from django.utils.translation import ugettext_lazy as _

    from core.views import *
    from core.models import User, Group

    # Utilisation de la protection par fonctions
    class Article(models.Model):

        title = models.CharField(_("title"), max_length=100)
        content = models.TextField(_("content"))

        # Donne ou non les droits d'édition des propriétés de l'objet
        # Un utilisateur dans le bureau AE aura tous les droits sur cet objet
        def is_owned_by(self, user):
            return user.is_board_member

        # Donne ou non les droits d'édition de l'objet
        # L'objet ne sera modifiable que par un utilisateur cotisant
        def can_be_edited_by(self, user):
            return user.is_subscribed

        # Donne ou non les droits de vue de l'objet
        # Ici, l'objet n'est visible que par un utilisateur connecté
        def can_be_viewed_by(self, user):
            return not user.user.is_anonymous

.. note::

    Si un utilisateur est autorisé à un niveau plus élevé que celui auquel il est testé, le système le détectera automatiquement et les droits lui seront accordé. Par défaut, les seuls utilisateurs ayant des droits quelconques sont les *superuser* de Django et les membres du bureau AE qui sont définis comme *owner*.

Appliquer les permissions
-------------------------

Dans un template
~~~~~~~~~~~~~~~~

Il existe trois fonctions de base sur lesquelles reposent les vérifications de permission. Elles sont disponibles dans le contexte par défaut du moteur de template et peuvent être utilisées à tout moment.

Tout d'abord, voici leur documentation et leur prototype.

.. autofunction:: core.views.can_edit_prop
.. autofunction:: core.views.can_edit
.. autofunction:: core.views.can_view

Voici un exemple d'utilisation dans un template :

.. code-block:: html+jinja

    {# ... #}
    {% if can_edit(club, user) %}
        <a href="{{ url('club:tools', club_id=club.id) }}">{{ club }}</a>
    {% endif %}

Dans une vue
~~~~~~~~~~~~

Généralement, les vérifications de droits dans les templates se limitent au liens à afficher puisqu'il ne faut pas mettre de logique autre que d'affichage à l'intérieur. C'est donc généralement au niveau des vues que cela a lieu.

Notre système s'appuie sur un système de mixin à hériter lors de la création d'une vue basée sur une classe. Ces mixins ne sont compatibles qu'avec les classes récupérant un objet ou une liste d'objet. Dans le cas d'un seul objet, une permission refusée est levée lorsque l'utilisateur n'as pas le droit de visionner la page. Dans le d'une liste d'objet, le mixin filtre les objets non autorisés et si aucun ne l'est l'utilisateur recevra une liste vide d'objet.

Voici un exemple d'utilisation en reprenant l'objet Article crée précédemment :

.. code-block:: python

    from django.views.generic import CreateView, ListView

    from core.views import CanViewMixin, CanCreateMixin

    from .models import Article

    ...

    # Il est important de mettre le mixin avant la classe héritée de Django
    # L'héritage multiple se fait de droite à gauche et les mixins ont besoin
    # d'une classe de base pour fonctionner correctement.
    class ArticlesListView(CanViewMixin, ListView):

        model = Article # On base la vue sur le modèle Article
        ...

    # Même chose pour une vue de création de l'objet Article
    class ArticlesCreateView(CanCreateMixin, CreateView):

        model = Article

Le système de permissions de propose plusieurs mixins différents, les voici dans leur intégralité.

.. autoclass:: core.views.CanCreateMixin
.. autoclass:: core.views.CanEditPropMixin
.. autoclass:: core.views.CanEditMixin
.. autoclass:: core.views.CanViewMixin
.. autoclass:: core.views.FormerSubscriberMixin
.. autoclass:: core.views.UserIsLoggedMixin