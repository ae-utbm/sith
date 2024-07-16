L'ORM de Django est puissant, très puissant, non par parce qu'il
est performant (après tout, ce n'est qu'une interface, le gros du boulot,
c'est la db qui le fait), mais parce qu'il permet d'écrire
de manière relativement simple un grand panel de requêtes.

De manière générale, puisqu'un ORM est un système
consistant à manipuler avec un code orienté-objet
une db relationnelle (c'est-à-dire deux paradigmes
qui ne fonctionnent absolument pas pareil),
on rencontre un des deux problèmes suivants :

- soit l'ORM n'offre pas assez d'abstraction,
  auquel cas, quand on veut faire des requêtes
  plus complexes qu'un `select` avec un `where`,
  on s'emmêle les pinceaux et on se dit que
  ça aurait été plus simple de le faire directement
  en SQL.
- soit l'ORM offre trop d'abstraction,
  auquel cas, on a tendance à ne pas prêter
  assez attention aux requêtes envoyées en base
  de données et on finit par se rendre compte
  que les temps d'attente explosent
  parce qu'on envoie trop de requêtes.

Django est dans ce deuxième cas.

C'est pourquoi nous ne parlerons pas ici
de son fonctionnement exact ni de toutes les fonctions
que l'on peut utiliser 
(la [doc officielle](https://docs.djangoproject.com/fr/stable/topics/db/queries/) fait déjà ça mieux que nous),
mais plutôt des pièges courants
et des astuces pour les éviter.

## Les `N+1 queries`

### Le problème

Normalement, quand on veut récupérer une liste,
on fait une requête et c'est fini.
Mais des fois, ça n'est pas si simple.
Par exemple, supposons que nous voulons
récupérer les 100 utilisateurs les plus riches,
avec leurs informations client :

```python
from core.models import User

for user in User.objects.order_by("-customer__amount")[:100]:
    print(user.customer.amount)
```

Combien de requêtes le bout de code suivant effectue-t-il ?
101\.
En deux pauvres lignes de code, nous avons demandé
à la base de données d'effectuer 101 requêtes.
Une requête toute seule n'est déjà une opération anodine,
alors je vous laisse imaginer ce que ça donne pour 101.

Si vous ne comprenez pourquoi ce nombre, c'est très simple :

- Une requête pour sélectionner nos 100 utilisateurs
- Une requête supplémentaire pour récupérer les informations
  client de chaque utilisateur, soit 100 requêtes.

En effet, les informations client sont stockées dans une
autre table, mais le fait d'établir un lien de clef
étrangère permet de manipuler `customer`
comme si c'était un membre à part entière de `User`.

Il est à noter cependant, que Django n'effectue une requête
que pour le premier accès à un membre d'une relation
de clef étrangère.
Toutes les fois suivantes, l'objet est déjà là,
et django le récupère :

```python
from core.models import User

# l'utilisateur le plus riche
user = User.objects.order_by("-customer__amount").first()  # <-- requête db
print(user.customer.amount)  # <-- requête db
print(user.customer.account_id)  # on a déjà récupéré `customer`, donc pas de requête
```

Ce n'est donc pas gravissime si vous faites cette
erreur quand vous manipulez un seul objet.
En revanche, quand vous en manipulez plusieurs,
il faut régler le problème.
Pour ça, il y a plusieurs méthodes, en fonction de votre cas.

### `select_related`

La méthode la plus basique consiste à annoter le queryset,
avec la méthode `select_related()`.
En faisant ça, Django fera une jointure sur l'autre table
et demandera des informations en plus
à la db lors de la requête.

De la sorte, lorsque vous appellerez le membre relié,
les informations seront déjà là.

```python
from core.models import User

richest = User.objects.order_by("-customer__amount")
for user in richest.select_related("customer")[:100]:
    print(user.customer)
```

Le code ci-dessus effectue une seule requête.
Chaque fois qu'on veut accéder à `customer`, c'est bon,
ça a déjà été récupéré à travers le `annotate`.

### `prefetch_related`

Maintenant, un cas plus compliqué.
Supposons que vous ne vouliez pas récupérer des informations
reliées par une relation One-to-One,
mais par une relation One-to-Many.

Par exemple, un utilisateur a un seul compte client,
mais il peut avoir plusieurs cotisations à son actif.
Et dans ces cas-là, `annotate` ne marche plus.
En effet, s'il peut exister plusieurs cotisations,
comment savoir laquelle on veut ?

Il faut alors utiliser un `prefetch_related`.
C'est un mécanisme un peu différent :
au lieu de faire une jointure et d'ajouter les informations
voulues dans la même requête, Django va effectuer
une deuxième requête pour récupérer les éléments de l'autre table,
puis, à partir de ces éléments, peupler la relation
de son côté.

C'est un mécanisme qui peut être un peu coûteux en mémoire
et qui demande une deuxième requête,
mais qui reste quand même largement préférable
à faire N requêtes en plus.

```python
from core.models import User

for user in User.objects.prefetch_related("subscriptions")[:100]:
    # c'est bon, la méthode prefetch a récupéré en avance les `subscriptions`
    print(user.subscriptions.all())
```

!!! danger

    La méthode `prefetch_related` ne marche que si vous
    utilisez la méthode `all()` pour accéder au membre.
    Si vous utilisez une autre méthode (comme `filter` ou `annotate`),
    alors Django effectuera une nouvelle requête,
    et vous retomberez dans le problème initial.

    ```python
    from core.models import User
    from django.db.models import Count
    
    for user in User.objects.prefetch_related("subscriptions")[:100]:
        # Le prefetch_related ne marche plus !
        print(user.subscriptions.annotate(count=Count("*")))
    ```

### Récupérer ce dont vous avez besoin

Des fois (souvent, même), penser explicitement
à la jointure est le meilleur choix.

En effet, vous remarquerez que dans tous
les exemples précédents, nous n'utilisions
qu'une partie des informations 
(par exemple, nous ne récupérions que la somme
d'argent sur les comptes, et éventuellement le numéro de compte).

Nous pouvons utiliser la méthode `annotate`
pour spécifier explicitement les données que l'on veut
joindre à notre requête.

Quand nous voulions récupérer les informations utilisateur,
nous aurions tout aussi bien pu écrire :

```python
from core.models import User
from django.db.models import F

richest = User.objects.order_by("-customer__amount")
for user in richest.annotate(amount=F("customer__amount"))[:100]:
    print(user.amount)
```

On aurait même pu réorganiser ça :
```python

from core.models import User
from django.db.models import F

richest = User.objects.annotate(amount=F("customer__amount")).order_by("-amount")
for user in richest[:100]:
    print(user.amount)
```

Ça peut sembler moins bien qu'un `select_related`, comme ça.
Des fois, c'est en effet moins bien, et des fois c'est mieux.
La comparaison est plus évidente avec le `prefetch_related`.

En effet, quand nous voulions récupérer
le nombre de cotisations des utilisateurs,
le `prefetch_related` ne marchait plus.
Pourtant, nous voulions récupérer une seule information.

Il aurait donc été suffisant d'écrire :
```python
from core.models import User
from django.db.models import Count

for user in User.objects.annotate(nb_subscriptions=Count("subscriptions"))[:100]:
    # Et là ça marche, en une seule requête.
    print(user.nb_subscriptions)
```

Faire une jointure, c'est normal en SQL.
Et pourtant avec Django on les oublie trop facilement.
Posez-vous toujours la question des données que vous pourriez
avoir besoin d'annoter, et vous éviterez beaucoup d'ennuis.

## Les aggrégations manquées

Il arrive souvent que l'on veuille une information qui
porte sur un ensemble d'objets de notre db.

Imaginons par exemple que nous voulons connaitre
la somme totale des ventes faites à un comptoir.

Nous avons tous suivi nos cours de programmation,
nous écrivons donc instinctivement :

```python
from counter.models import Counter

foyer = Counter.objects.get(name="Foyer")
total_amount = sum(
    sale.amount * sale.unit_price
    for sale in foyer.sellings.all()
)
```

On pourrait penser qu'il n'y a pas de problème.
Après tout, on ne fait qu'une seule requête.
Eh bien si, il y a un problème :
on fait beaucoup de choses en trop.

Concrètement, on demande à la base de données
de renvoyer toutes les informations,
ce qui rallonge inutilement la durée
de l'échange entre le serveur et la db,
puis on perd du temps à convertir ces informations
en objets Python (opération qui a un coût également),
et enfin on reperd du temps à calculer en Python
quelque chose que la db aurait pu calculer
à notre plus bien plus vite.

Nous aurions dû aggréger la requête,
avec la méthode `aggregate` :

```python
from counter.models import Counter
from django.db.models import Sum, F

foyer = Counter.objects.get(name="Foyer")
total_amount = (
    foyer.sellings.aggregate(amount=Sum(F("amount") * F("unit_price"), default=0))
)["amount__sum"]
```

En effectuant cette requête, la base de données nous renverra exactement
l'information dont nous avons besoin.
Et de notre côté, nous n'aurons pas à faire de traitement en plus.


