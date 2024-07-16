
## Les permissions

Le site n'utilise pas le système de permissions intégré de Django,
mais un système de conception maison.

### Protéger un modèle

La gestion des permissions se fait directement par modèle.
Il existe trois niveaux de permission :

- Éditer des propriétés de l'objet
- Éditer certaines valeurs l'objet
- Voir l'objet

Chacune de ces permissions est vérifiée par une méthode
dédiée de la classe `User` :

- Editer les propriéts : `User.is_owner(obj)`
- Editer les valeurs : `User.can_edit(obj)`
- Voir : `User.can_view(obj)`

Ces méthodes vont alors résoudre les permissions
dans cet ordre :

1. Si l'objet possède une méthode `can_be_viewed_by(user)` 
   (ou `can_be_edited_by(user)`, ou `is_owned_by(user)`)
   et que son appel renvoie `True`, l'utilisateur a la permission requise.
2. Sinon, si le modèle de l'objet possède un attribut `view_groups`
   (ou `edit_groups`, ou `owner_group`) et que l'utilisateur
   est dans l'un des groupes indiqués, il a la permission requise.
3. Sinon, on regarde si l'utilisateur a la permission de niveau supérieur
   (les droits `owner` impliquent les droits d'édition, et les droits
   d'édition impliquent les droits de vue).
4. Si aucune des étapes si dessus ne permet d'établir que l'utilisateur
   n'a la permission requise, c'est qu'il ne l'a pas.

Voici un exemple d'implémentation de ce système :

=== "Avec les méthodes"

    ```python
    from django.db import models
    from django.utils.translation import gettext_lazy as _

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
            return not user.is_anonymous
    ```

=== "Avec les groupes de permission"

    ```python
    from django.db import models
    from django.conf import settings
    from django.utils.translation import gettext_lazy as _

    from core.models import User, Group

    class Article(models.Model):
        title = models.CharField(_("title"), max_length=100)
        content = models.TextField(_("content"))

        # relation one-to-many
        # Groupe possédant l'objet
        # Donne les droits d'édition des propriétés de l'objet
        owner_group = models.ForeignKey(
            Group, related_name="owned_articles", default=settings.SITH_GROUP_ROOT_ID
        )
        
        # relation many-to-many
        # Tous les groupes qui seront ajouté dans ce champ auront les droits d'édition de l'objet
        edit_groups = models.ManyToManyField(
            Group,
            related_name="editable_articles",
            verbose_name=_("edit groups"),
            blank=True,
        )
    
        # relation many-to-many
        # Tous les groupes qui seront ajouté dans ce champ auront les droits de vue de l'objet
        view_groups = models.ManyToManyField(
            Group,
            related_name="viewable_articles",
            verbose_name=_("view groups"),
            blank=True,
        )
    ```

### Appliquer les permissions

#### Dans un template

Il existe trois fonctions de base sur lesquelles 
reposent les vérifications de permission. 
Elles sont disponibles dans le contexte par défaut du 
moteur de template et peuvent être utilisées à tout moment.

- `can_edit_prop(obj, user)` : équivalent de `obj.is_owned_by(user)`
- `can_edit(obj, user)` : équivalent de `obj.can_be_edited_by(user)`
- `can_view(obj, user)` : équivalent de `obj.can_be_viewed_by(user)`

Voici un exemple d'utilisation dans un template :

```jinja
{# ... #}
{% if can_edit(club, user) %}
    <a href="{{ url('club:tools', club_id=club.id) }}">{{ club }}</a>
{% endif %}
```

#### Dans une vue

Généralement, les vérifications de droits dans les templates
se limitent aux urls à afficher puisqu'il 
ne faut normalement pas mettre de logique autre que d'affichage à l'intérieur
(en réalité, c'est un principe qu'on a beaucoup violé, mais promis on le fera plus).
C'est donc habituellement au niveau des vues que cela a lieu.

Notre système s'appuie sur un système de mixin
à hériter lors de la création d'une vue basée sur une classe.
Ces mixins ne sont compatibles qu'avec les classes récupérant
un objet ou une liste d'objet.
Dans le cas d'un seul objet, 
une permission refusée est levée lorsque l'utilisateur
n'a pas le droit de visionner la page. 
Dans le cas d'une liste d'objet,
le mixin filtre les objets non autorisés et si aucun ne l'est,
l'utilisateur recevra une liste vide d'objet.

Voici un exemple d'utilisation en reprenant l'objet Article crée précédemment :

```python
from django.views.generic import CreateView, ListView

from core.views import CanViewMixin, CanCreateMixin

from com.models import WeekmailArticle

# Il est important de mettre le mixin avant la classe héritée de Django
# L'héritage multiple se fait de droite à gauche et les mixins ont besoin
# d'une classe de base pour fonctionner correctement.
class ArticlesListView(CanViewMixin, ListView):
  model = WeekmailArticle

  
# Même chose pour une vue de création de l'objet Article
class ArticlesCreateView(CanCreateMixin, CreateView):
  model = WeekmailArticle
```

Les mixins suivants sont implémentés :

- `CanCreateMixin` : l'utilisateur peut-il créer l'objet ?
- `CanEditPropMixin` : l'utilisateur peut-il éditer les propriétés de l'objet ?
- `CanEditMixin` : L'utilisateur peut-il éditer l'objet ?
- `CanViewMixin` : L'utilisateur peut-il voir l'objet ?
- `UserIsRootMixin` : L'utilisateur a-t-il les droit root ?
- `FormerSubscriberMixin` : L'utilisateur a-t-il déjà été cotisant ?
- `UserIsLoggedMixin` : L'utilisateur est-il connecté ?
  (à éviter ; préférez `LoginRequiredMixin`, fourni par Django)

!!!danger "Performance"

   Ce système maison de permissions ne rend pas trop mal, d'un point de vue esthétique.
   Mais d'un point de vue performance, c'est un désastre.
   Vérifier une seule permission peut demander plusieurs requêtes à la db.
   Et chaque vérification recommence dès le début.
   Il n'y a aucune jointure en db.
   Le mieux qu'on a trouvé comme pansement sur ça, c'est utiliser le cache,
   mais c'est seulement un pansement, qui ne rattrape pas les erreurs architecturales.

   Sur une vue où on manipule un seul objet, passe encore.
   Mais sur les `ListView`, on peut arriver à des temps
   de réponse extrêmement élevés.
   
   Faites donc doublement, triplement, quadruplement attention,
   quand vous manipulez le système de permissions.

