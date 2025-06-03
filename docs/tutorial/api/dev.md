
Pour l'API, nous utilisons `django-ninja` et sa surcouche `django-ninja-extra`.
Ce sont des librairies relativement simples et qui présentent
l'immense avantage d'offrir des mécanismes de validation et de sérialisation
de données à la fois simples et expressifs.

## Schéma de données

Le cœur de django-ninja étant sa validation de données grâce à Pydantic,
le développement de l'API commence par l'écriture de ses schémas de données.

Pour en comprendre le fonctionnement, veuillez consulter 
[la doc de django-ninja](https://django-ninja.dev/guides/response/).

Il est également important de consulter 
[la doc de pydantic](https://docs.pydantic.dev/latest/).

Notre surcouche par-dessus les schémas de django-ninja est relativement mince.
Elle ne comprend que [UploadedImage][core.schemas.UploadedImage], qui hérite de 
[`UploadedFile`](https://django-ninja.dev/guides/input/file-params/?h=upl)
pour le restreindre uniquement aux images.

## Authentification et permissions

### Authentification

Notre API offre deux moyens d'authentification :

- par cookie de session (la méthode par défaut de django)
- par clef d'API

La plus grande partie des routes de l'API utilisent la méthode par cookie de session.

Pour placer une route d'API derrière l'une de ces méthodes (ou bien les deux),
utilisez l'attribut `auth` et les classes `SessionAuth` et 
[`ApiKeyAuth`][apikey.auth.ApiKeyAuth].

!!!example

    ```python
    @api_controller("/foo")
    class FooController(ControllerBase):
        # Cette route sera accessible uniquement avec l'authentification
        # par cookie de session
        @route.get("", auth=[SessionAuth()])
        def fetch_foo(self, club_id: int): ...

        # Et celle-ci sera accessible peut importe la méthode d'authentification
        @route.get("/bar", auth=[SessionAuth(), ApiKeyAuth()])
        def fetch_bar(self, club_id: int): ...
    ```

### Permissions

Si l'utilisateur est connecté, ça ne veut pas dire pour autant qu'il a accès à tout.
Une fois qu'il est authentifié, il faut donc vérifier ses permissions.

Pour cela, nous utilisons une surcouche
par-dessus `django-ninja`, le système de permissions de django
et notre propre système.
Cette dernière est documentée [ici](../perms.md).

### Limites des clefs d'API

#### Incompatibilité avec certaines permissions

Le système des clefs d'API est apparu très tard dans l'histoire du site
(en P25, 10 ans après le début du développement).
Il s'agit ni plus ni moins qu'un système d'authentification parallèle fait maison,
devant interagir avec un système de permissions ayant connu lui-même
une histoire assez chaotique.

Assez logiquement, on ne peut pas tout faire : 
il n'est pas possible que toutes les routes acceptent 
l'authentification par clef d'API.

Cette impossibilité provient majoritairement d'une incompatibilité
entre cette méthode d'authentification et le système de permissions
(qui n'a pas été prévu pour l'implémentation d'un client d'API).
Les principaux points de friction sont :

- `CanView` et `CanEdit`, qui se basent `User.can_view` et `User.can_edit`,
  qui peuvent eux-mêmes se baser sur les méthodes `can_be_viewed_by`
  et `can_be_edited_by` des différents modèles.
  Or, ces dernières testent spécifiquement la relation entre l'objet et un `User`.
  Ce comportement est possiblement changeable, mais au prix d'un certain travail
  et au risque de transformer encore plus notre système de permissions
  en usine à gaz.
- `IsSubscriber` et `OldSubscriber`, qui vérifient qu'un utilisateur est ou
  a été cotisant.
  Or, une clef d'API est liée à un client d'API, pas à un utilisateur.
  Par définition, un client d'API ne peut pas être cotisant.
- `IsLoggedInCounter`, qui utilise encore un autre système 
  d'authentification maison et qui n'est pas fait pour être utilisé en dehors du site.

#### Incompatibilité avec les tokens csrf

Le [CSRF (*cross-site request forgery*)](https://fr.wikipedia.org/wiki/Cross-site_request_forgery)
est un des multiples facteurs d'attaque sur le web.
Heureusement, Django vient encore une fois à notre aide,
avec des mécanismes intégrés pour s'en protéger.
Ceux-ci incluent notamment un système de 
[token CSRF](https://docs.djangoproject.com/fr/stable/ref/csrf/)
à fournir dans les requêtes POST/PUT/PATCH.

Ceux-ci sont bien adaptés au cycle requêtes/réponses
typique de l'expérience utilisateur sur un navigateur, 
où les requêtes POST sont toujours effectuées après une requête
GET au cours de laquelle on a pu récupérer un token csrf.
Cependant, le flux des requêtes sur une API est bien différent ;
de ce fait, il est à attendre que les requêtes POST envoyées à l'API
par un client externe n'aient pas de token CSRF et se retrouvent 
donc bloquées.

Pour ces raisons, l'accès aux requêtes POST/PUT/PATCH de l'API
par un client externe ne marche pas.

## Créer un client et une clef d'API

Le site n'a actuellement pas d'interface permettant à ses utilisateurs
de créer une application et des clefs d'API.

C'est volontaire : tant que le système ne sera pas suffisamment mature,
toute attribution de clef d'API doit passer par le pôle info.

Cette opération se fait au travers de l'interface admin.

Pour commencer, créez un client d'API, en renseignant son nom,
son propriétaire (l'utilisateur qui vous a demandé de le créer)
et les groupes qui lui sont attribués.
Ces groupes sont les mêmes que ceux qui sont attribués aux utilisateurs,
ce qui permet de réutiliser une partie du système d'authentification.

!!!warning

    N'attribuez pas les groupes "anciens cotisants" et "cotisants"
    aux clients d'API.
    Un client d'API géré comme un cotisant, ça n'a aucun sens.

    Evitez également de donner à des clients d'API des droits
    autres que ceux de lecture sur le site.

    Et surtout, n'attribuez jamais le group Root à un client d'API.

Une fois le client d'API créé, créez-lui une clef d'API.
Renseignez uniquement son nom et le client d'API auquel elle est lié.
La valeur de cette clef d'API est automatiquement générée
et affichée en haut de la page une fois la création complétée.

Notez bien la valeur de la clef d'API et transmettez-la à la personne
qui en a besoin.
Dites-lui bien de garder cette clef en lieu sûr !
Si la clef est perdue, il n'y a pas moyen de la récupérer,
vous devrez en recréer une.


