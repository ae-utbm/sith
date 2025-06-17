
## Objectifs du système de permissions

Les permissions attendues sur le site sont relativement spécifiques.
L'accès à une ressource peut se faire selon un certain nombre
de paramètres différents :

`L'état de la ressource`
:   Certaines ressources
    sont visibles par tous les cotisants (voire tous les utilisateurs),
    à condition qu'elles aient passé une étape de modération.
    La visibilité des ressources non-modérées nécessite des permissions
    supplémentaires.

`L'appartenance à un groupe`
:   Les groupes Root, Admin Com, Admin SAS, etc.
    sont associés à des jeux de permissions.
    Par exemple, les membres du groupe Admin SAS ont tous les droits sur
    les ressources liées au SAS : ils peuvent voir,
    créer, éditer, supprimer et éventuellement modérer
    des images, des albums, des identifications de personnes...
    Il en va de même avec les admins Com pour la communication,
    les admins pédagogie pour le guide des UEs et ainsi de suite.
    Quant aux membres du groupe Root, ils ont tous les droits
    sur toutes les ressources du site.

`Le statut de la cotisation`
:   Les non-cotisants n'ont presque aucun
    droit sur les ressources du site (ils peuvent seulement en voir une poignée),
    les anciens cotisants peuvent voir un grand nombre de ressources
    et les cotisants actuels ont la plupart des droits qui ne sont
    pas liés à un club ou à l'administration du site.

`L'appartenance à un club`
:   Être dans un club donne le droit
    de voir la plupart des ressources liées au club dans lequel ils
    sont ; être dans le bureau du club donne en outre des droits
    d'édition et de création sur ces ressources.

`Être l'auteur ou le possesseur d'une ressource`
:   Certaines ressources, comme les nouvelles, 
    enregistrent l'utilisateur qui les a créées ;
    ce dernier a les droits de voir, de modifier et éventuellement
    de supprimer ses ressources, quand bien même
    elles ne seraient pas visibles pour les utilisateurs normaux
    (par exemple, parce qu'elles ne sont pas encore modérées.)


Le système de permissions inclus par défaut dans django
permet de modéliser aisément l'accès à des ressources au niveau
de la table.
Ainsi, il n'est pas compliqué de gérer les permissions liées
aux groupes d'administration.

Cependant, une surcouche est nécessaire dès lors que l'on veut
gérer les droits liés à une ligne en particulier
d'une table de la base de données.

Nous essayons le plus possible de nous tenir aux fonctionnalités
de django, sans pour autant hésiter à nous rabattre sur notre
propre surcouche dès lors que les permissions attendues
deviennent trop spécifiques pour être gérées avec juste django.

!!!info "Un peu d'histoire"

    Les permissions du site n'ont pas toujours été gérées
    avec un mélange de fonctionnalités de django et de notre
    propre code.
    Pendant très longtemps, seule la surcouche était utilisée,
    ce qui menait souvent à des vérifications de droits
    inefficaces et à une gestion complexe de certaines
    parties qui auraient pu être manipulées beaucoup plus simplement.

    En plus de ça, les permissions liées à la plupart
    des groupes se faisait de manière hardcodée :
    plutôt que d'associer un groupe à un jeu de permission
    et de faire une jointure en db sur les groupes de l'utilisateur
    ayant cette permissions,
    on conservait la clef primaire du groupe dans la config
    et on vérifiait en dur dans le code que l'utilisateur
    était un des groupes voulus.

    Ce système possédait le triple désavantage de prendre énormément
    de temps, d'être extrêmement limité (de fait, si tout est hardcodé,
    on est obligé d'avoir le moins de groupes possibles pour que ça reste
    gérable) et d'être désespérément dangereux (par exemple : fin novembre 2024,
    une erreur dans le code a donné les accès à la création des cotisations
    à tout le monde ; mi-octobre 2019, le calcul des permissions des etickets
    pouvait faire tomber le site, cf. 
    [ce topic du forum](https://ae.utbm.fr/forum/topic/17943/?page=1msg2277272))
    
## Accès à toutes les ressources d'une table

Gérer ce genre d'accès (par exemple : voir toutes les nouvelles
ou pouvoir supprimer n'importe quelle photo)
est exactement le problème que le système de permissions de django résout.
Nous utilisons donc ce système dans ce genre de situations.

!!!note

    Nous décrivons ci-dessous l'usage que nous faisons du système
    de permissions de django,
    mais la seule source d'information complète et pleinement fiable
    sur le fonctionnement réel de ce système est 
    [la documentation de django](https://docs.djangoproject.com/fr/stable/topics/auth/default/).

### Permissions d'un modèle

Par défaut, django crée quatre permissions pour chaque table de la base de données :

- `add_<nom de la table>` : créer un objet dans cette table
- `view_<nom de la table>` : voir le contenu de la table
- `change_<nom de la table>` : éditer des objets de la table
- `delete_<nom de la table>` : supprimer des objets de la table

Ces permissions sont créées au même moment que le modèle.
Si la table existe en base de données, ces permissions existent aussi.

Il est également possible de rajouter nos propres permissions,
directement dans les options Meta du modèle.
Par exemple, prenons le modèle suivant :

```python
from django.db import models

class News(models.Model):
    # ...

    class Meta:
        permissions = [
            ("moderate_news", "Can moderate news"),
            ("view_unmoderated_news", "Can view non-moderated news"),
        ]
```

Ce dernier aura les permissions : `view_news`, `add_news`, `change_news`,
`delete_news`, `moderate_news` et `view_unmoderated_news`.

### Utilisation des permissions d'un modèle

Pour vérifier qu'un utilisateur a une permission,
on utilise les fonctions suivantes :

- `User.has_perm(perm)` : retourne `True` si l'utilisateur
  a la permission voulue, sinon `False`
- `User.has_perms([perm_a, perm_b, perm_c])` : retourne `True` si l'utilisateur
  a toutes les permissions voulues, sinon `False`.

Ces fonctions attendent un string suivant le format :
`<nom de l'application>.<nom de la permission>`.
Par exemple, la permission pour vérifier qu'un utilisateur
peut modérer une nouvelle sera : `com.moderate_news`.

Ces fonctions sont utilisables aussi bien dans les templates Jinja
que dans le code Python :

=== "Jinja"

    ```jinja
    {% if user.has_perm("com.moderate_news") %}
        <form method="post" action="{{ url("com:news_moderate", news_id=387) }}">
            <input type="submit" value="Modérer" />
        </form>
    {% endif %}
    ```

=== "Python"

    ```python
    from com.models import News
    from core.models import User

    
    user = User.objects.get(username="bibou")
    news = News.objects.get(id=387)
    if user.has_perm("com.moderate_news"):
        news.is_moderated = True
        news.save()
    else:
        raise PermissionDenied
    ```        

Pour utiliser ce système de permissions dans une class-based view
(c'est-à-dire la plus grande partie de nos vues),
Django met à disposition `PermissionRequiredMixin`,
qui restreint l'accès à la vue aux utilisateurs ayant
la ou les permissions requises.
Pour les vues sous forme de fonction, il y a le décorateur
`permission_required`.

=== "Class-Based View"

    ```python
    from com.models import News
    
    from django.contrib.auth.mixins import PermissionRequiredMixin
    from django.shortcuts import redirect
    from django.urls import reverse
    from django.views import View
    from django.views.generic.detail import SingleObjectMixin
    
    class NewsModerateView(PermissionRequiredMixin, SingleObjectMixin, View):
        model = News
        pk_url_kwarg = "news_id"
        permission_required = "com.moderate_news"
        # On peut aussi fournir plusieurs permissions, par exemple :
        # permission_required = ["com.moderate_news", "com.delete_news"]
    
        def post(self, request, *args, **kwargs):
            # Si nous sommes ici, nous pouvons être certains que l'utilisateur
            # a la permission requise
            obj = self.get_object()
            obj.is_moderated = True
            obj.save()
            return redirect(reverse("com:news_list"))
    ```

=== "Function-based view"

    ```python
    from com.models import News
    
    from django.contrib.auth.decorators import permission_required
    from django.shortcuts import get_object_or_404, redirect
    from django.urls import reverse
    from django.views.decorators.http import require_POST
    
    @permission_required("com.moderate_news")
    @require_POST
    def moderate_news(request, news_id: int):
        # Si nous sommes ici, nous pouvons être certains que l'utilisateur
        # a la permission requise
        news = get_object_or_404(News, id=news_id)
        news.is_moderated = True
        news.save()
        return redirect(reverse("com:news_list"))
    ```

## Accès à des éléments en particulier

### Accès à l'auteur de la ressource

Dans ce genre de cas, on peut identifier trois acteurs possibles :

- les administrateurs peuvent accéder à toutes les ressources,
  y compris non-modérées
- l'auteur d'une ressource non-modérée peut y accéder
- Les autres utilisateurs ne peuvent pas voir les ressources
  non-modérées dont ils ne sont pas l'auteur

Dans ce genre de cas, on souhaite donc accorder l'accès aux
utilisateurs qui ont la permission globale, selon le système
décrit plus haut, ou bien à l'auteur de la ressource.

Pour cela, nous avons le mixin `PermissionOrAuthorRequired`.
Ce dernier va effectuer les mêmes vérifications que `PermissionRequiredMixin`
puis, si l'utilisateur n'a pas la permission requise, vérifier
s'il est l'auteur de la ressource.

```python
from com.models import News
from core.auth.mixins import PermissionOrAuthorRequiredMixin

from django.views.generic import UpdateView

class NewsUpdateView(PermissionOrAuthorRequiredMixin, UpdateView):
    model = News
    pk_url_kwarg = "news_id"
    permission_required = "com.change_news"
    author_field = "author"  # (1)!
```

1. Nom du champ du modèle utilisé comme clef étrangère vers l'auteur.
   Par exemple, ici, la permission sera accordée si
   l'utilisateur connecté correspond à l'utilisateur
   désigné par `News.author`.

### Accès en fonction de règles plus complexes

Tout ce que nous avons décrit précédemment permet de couvrir
la plupart des cas simples.
Cependant, il arrivera souvent que les permissions attendues soient
plus complexes.
Dans ce genre de cas, on rentre entièrement dans notre surcouche.

#### Implémentation dans les modèles

La gestion de ce type de permissions se fait directement par modèle.
Il en existe trois niveaux :

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

    class Article(models.Model):

        title = models.CharField(_("title"), max_length=100)
        content = models.TextField(_("content"))

        def is_owned_by(self, user):  # (1)!
            return user.is_board_member

        def can_be_edited_by(self, user):  # (2)!
            return user.is_subscribed

        def can_be_viewed_by(self, user):  # (3)!
            return not user.is_anonymous
    ```

    1. Donne ou non les droits d'édition des propriétés de l'objet.
       Ici, un utilisateur dans le bureau AE aura tous les droits sur cet objet
    2. Donne ou non les droits d'édition de l'objet
       Ici, l'objet ne sera modifiable que par un utilisateur cotisant
    3. Donne ou non les droits de vue de l'objet
       Ici, l'objet n'est visible que par un utilisateur connecté

    !!!note

        Dans cet exemple, nous utilisons des permissions très simples
        pour que vous puissiez constater le squelette de ce système,
        plutôt que la logique de validation dans ce cas particulier.

        En réalité, il serait ici beaucoup plus approprié de
        donner les permissions `com.delete_article` et
        `com.change_article_properties` (en créant ce dernier 
        s'il n'existe pas encore) au groupe du bureau AE, 
        de donner également la permission `com.change_article`
        au groupe `Cotisants` et enfin de restreindre l'accès 
        aux vues d'accès aux articles avec `LoginRequiredMixin`.
        

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
        owner_group = models.ForeignKey(  # (1)!
            Group, related_name="owned_articles", default=settings.SITH_GROUP_ROOT_ID
        )
        
        # relation many-to-many
        edit_groups = models.ManyToManyField(  # (2)!
            Group,
            related_name="editable_articles",
            verbose_name=_("edit groups"),
            blank=True,
        )
    
        # relation many-to-many
        view_groups = models.ManyToManyField(  # (3)!
            Group,
            related_name="viewable_articles",
            verbose_name=_("view groups"),
            blank=True,
        )
    ```

    1. Groupe possédant l'objet
       Donne les droits d'édition des propriétés de l'objet.
       Il ne peut y avoir qu'un seul groupe `owner` par objet.
    2. Tous les groupes ayant droit d'édition sur l'objet.
       Il peut y avoir autant de groupes d'édition que l'on veut par objet.
    3. Tous les groupes ayant droit de voir l'objet.
       Il peut y avoir autant de groupes de vue que l'on veut par objet.
        

#### Application dans les templates

Il existe trois fonctions de base sur lesquelles 
reposent les vérifications de permission. 
Elles sont disponibles dans le contexte par défaut du 
moteur de template et peuvent être utilisées à tout moment.

- [can_edit_prop(obj, user)][core.auth.mixins.can_edit_prop] : équivalent de `obj.is_owned_by(user)`
- [can_edit(obj, user)][core.auth.mixins.can_edit] : équivalent de `obj.can_be_edited_by(user)`
- [can_view(obj, user)][core.auth.mixins.can_view] : équivalent de `obj.can_be_viewed_by(user)`

Voici un exemple d'utilisation dans un template :

```jinja
{# ... #}
{% if can_edit(club, user) %}
    <a href="{{ url('club:tools', club_id=club.id) }}">{{ club }}</a>
{% endif %}
```

#### Application dans les vues

Généralement, les vérifications de droits dans les templates
se limitent aux urls à afficher puisqu'il 
ne faut normalement pas mettre de logique autre que d'affichage à l'intérieur
(en réalité, c'est un principe qu'on a beaucoup violé, mais promis on le fera plus).
C'est donc habituellement au niveau des vues que cela a lieu.

Pour cela, nous avons rajouté des mixins
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
from django.views.generic import CreateView, DetailView

from core.auth.mixins import CanViewMixin, CanCreateMixin

from com.models import WeekmailArticle


# Il est important de mettre le mixin avant la classe héritée de Django
# L'héritage multiple se fait de droite à gauche et les mixins ont besoin
# d'une classe de base pour fonctionner correctement.
class ArticlesDetailView(CanViewMixin, DetailView):
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

### Filtrage des querysets

Récupérer tous les objets d'un queryset et vérifier pour chacun que
l'utilisateur a le droit de les voir peut-être excessivement
coûteux en ressources
(cf. l'encart ci-dessus).

Lorsqu'il est nécessaire de récupérer un certain nombre
d'objets depuis la base de données, il est donc préférable
de filtrer directement depuis le queryset.

Pour cela, certains modèles, tels que [Picture][sas.models.Picture] 
peuvent être filtrés avec la méthode de queryset `viewable_by`.
Cette dernière s'utilise comme n'importe quelle autre méthode
de queryset :

```python
from sas.models import Picture
from core.models import User

user = User.objects.get(username="bibou")
pictures = Picture.objects.viewable_by(user)
```

Le résultat de la requête contiendra uniquement des éléments
que l'utilisateur sélectionné a effectivement le droit de voir.

Si vous désirez utiliser cette méthode sur un modèle
qui ne la possède pas, il est relativement facile de l'écrire :

```python
from typing import Self

from django.db import models

from core.models import User


class NewsQuerySet(models.QuerySet):  # (1)!
    def viewable_by(self, user: User) -> Self:
        if user.has_perm("com.view_unmoderated_news"):
            # si l'utilisateur peut tout voir, on retourne tout
            return self
        # sinon, on retourne les nouvelles modérées ou dont l'utilisateur
        # est l'auteur
        return self.filter(
            models.Q(is_moderated=True)
            | models.Q(author=user)
        )


class News(models.Model):
    is_moderated = models.BooleanField(default=False)
    author = models.ForeignKey(User, on_delete=models.PROTECT)
    # ...

    objects = NewsQuerySet.as_manager()  # (2)!

    class Meta:
        permissions = [("view_unmoderated_news", "Can view non moderated news")]
```

1. On crée un `QuerySet` maison, dans lequel on définit la méthode `viewable_by`
2. Puis, on attache ce `QuerySet` à notre modèle

!!!note

    Pour plus d'informations sur la création de `QuerySet` personnalisés, voir
    [la documentation de django](https://docs.djangoproject.com/fr/stable/topics/db/managers/)

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
dans [cette partie](../reference/api/perms.md).
