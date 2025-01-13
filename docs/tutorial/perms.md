
## Les permissions

Le fonctionnement de l'AE ne permet pas d'utiliser le système de permissions
intégré à Django tel quel. Lors de la conception du Sith, ce qui paraissait le
plus simple à l'époque était de concevoir un système maison afin de se calquer
sur ce que faisait l'ancien site.

### Protéger un modèle

La gestion des permissions se fait directement par modèle.
Il existe trois niveaux de permission :

- Éditer des propriétés de l'objet
- Éditer certaines valeurs l'objet
- Voir l'objet

Chacune de ces permissions est vérifiée par une méthode
dédiée de la classe [User][core.models.User] :

- Editer les propriéts : [User.is_owner(obj)][core.models.User.is_owner]
- Editer les valeurs : [User.can_edit(obj)][core.models.User.can_edit]
- Voir : [User.can_view(obj)][core.models.User.can_view]

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

- [can_edit_prop(obj, user)][core.views.can_edit_prop] : équivalent de `obj.is_owned_by(user)`
- [can_edit(obj, user)][core.views.can_edit] : équivalent de `obj.can_be_edited_by(user)`
- [can_view(obj, user)][core.views.can_view] : équivalent de `obj.can_be_viewed_by(user)`

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

from core.auth.mixins import CanViewMixin, CanCreateMixin

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

- [CanCreateMixin][core.auth.mixins.CanCreateMixin] : l'utilisateur peut-il créer l'objet ?
  Ce mixin existe, mais est déprécié et ne doit plus être utilisé !
- [CanEditPropMixin][core.auth.mixins.CanEditPropMixin] : l'utilisateur peut-il éditer les propriétés de l'objet ?
- [CanEditMixin][core.auth.mixins.CanEditMixin] : L'utilisateur peut-il éditer l'objet ?
- [CanViewMixin][core.auth.mixins.CanViewMixin] : L'utilisateur peut-il voir l'objet ?
- [FormerSubscriberMixin][core.auth.mixins.FormerSubscriberMixin] : L'utilisateur a-t-il déjà été cotisant ?

!!!danger "CanCreateMixin"

    L'usage de `CanCreateMixin` est dangereux et ne doit en aucun cas être
    étendu.
    La façon dont ce mixin marche est qu'il valide le formulaire
    de création et crée l'objet sans le persister en base de données, puis
    vérifie les droits sur cet objet non-persisté.
    Le danger de ce système vient de multiples raisons :
      - Les vérifications se faisant sur un objet non persisté,
        l'utilisation de mécanismes nécessitant une persistance préalable
        peut mener à des comportements indésirés, voire à des erreurs.
      - Les développeurs de django ayant tendance à restreindre progressivement
        les actions qui peuvent être faites sur des objets non-persistés,
        les mises-à-jour de django deviennent plus compliquées.
      - La vérification des droits ne se fait que dans les requêtes POST,
        à la toute fin de la requête.
        Tout ce qui arrive avant n'est absolument pas protégé.
        Toute opération (même les suppressions et les créations) qui ont
        lieu avant la persistance de l'objet seront appliquées,
        même sans permission.
      - Si un développeur du site fait l'erreur de surcharger
        la méthode `form_valid` (ce qui est plutôt courant,
        lorsqu'on veut accomplir certaines actions 
        quand un formulaire est valide), on peut se retrouver
        dans une situation où l'objet est persisté sans aucune protection.

!!!danger "Performance"

    Ce système maison de permissions fonctionne et répond aux attentes de l'époque de sa conception.  
    Mais d'un point de vue performance, il est souvent plus que problématique.
    En effet, toutes les permissions sont dynamiquement calculées et
    nécessitent plusieurs appels en base de données qui ne se résument pas à
    une « simple » jointure mais à plusieurs requêtes différentes et
    difficiles à optimiser. De plus, à chaque calcul de permission, il est
    nécessaire de recommencer tous les calculs depuis le début.  
    La solution à ça est de mettre du cache de session sur les tests effectués
    récemment, mais cela engendre son autre lot de problèmes.

    Sur une vue où on manipule un seul objet, passe encore.
    Mais sur les `ListView`, on peut arriver à des temps
    de réponse extrêmement élevés.

## API

L'API utilise son propre système de permissions.
Ce n'est pas encore un autre système en parallèle, mais un wrapper
autour de notre système de permissions, afin de l'adapter aux besoins
de l'API.

En effet, l'interface attendue pour manipuler le plus aisément
possible les permissions des routes d'API avec la librairie que nous
utilisons est différente de notre système, tout en restant adaptable.
(Pour plus de détail, 
[voir la doc de la lib](https://eadwincode.github.io/django-ninja-extra/api_controller/api_controller_permission/)).

Si vous avez bien suivi ce qui a été dit plus haut,
vous ne devriez pas être perdu, étant donné
que le système de permissions de l'API utilise
des noms assez similaires : `IsInGroup`, `IsRoot`, `IsSubscriber`...
Vous pouvez trouver des exemples d'utilisation de ce système
dans [cette partie](../reference/core/api_permissions.md).
