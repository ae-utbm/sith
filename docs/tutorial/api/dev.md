Pour l'API, nous utilisons `django-ninja` et sa surcouche `django-ninja-extra`.
Ce sont des librairies relativement simples et qui présentent
l'immense avantage d'offrir des mécanismes de validation et de sérialisation
de données à la fois simples et expressifs.

## Dossiers et fichiers

L'API possède une application (`api`) 
à la racine du projet, contenant des utilitaires 
et de la configuration partagée par toutes les autres applications.
C'est la pièce centrale de notre API, mais ce n'est pas là que
vous trouverez les routes de l'API.

Les routes en elles-mêmes sont contenues dans les autres applications,
de manière thématiques :
les routes liées aux clubs sont dans `club`, les routes liées
aux photos dans `sas` et ainsi de suite.

Les fichiers liés à l'API dans chaque application sont
`schemas.py` et `api.py`.
`schemas.py` contient les schémas de validation de données
et `api.py` contient les contrôleurs de l'API.


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
Cette dernière est donc activée par défaut.

Pour changer la méthode d'authentification,
utilisez l'attribut `auth` et les classes `SessionAuth` et 
[`ApiKeyAuth`][api.auth.ApiKeyAuth].

!!!example

    ```python
    @api_controller("/foo")
    class FooController(ControllerBase):
        # Cette route sera accessible uniquement avec l'authentification
        # par clef d'API
        @route.get("", auth=[ApiKeyAuth()])
        def fetch_foo(self, club_id: int): ...

        # Celle-ci sera accessible avec les deux méthodes d'authentification
        @route.get("/bar", auth=[ApiKeyAuth(), SessionAuth()])
        def fetch_bar(self, club_id: int): ...

        # Et celle-ci sera accessible aussi aux utilisateurs non-connectés
        @route.get("/public", auth=None)
        def fetch_public(self, club_id: int): ...
    ```

### Permissions

Si l'utilisateur est connecté, ça ne veut pas dire pour autant qu'il a accès à tout.
Une fois qu'il est authentifié, il faut donc vérifier ses permissions.

Pour cela, nous utilisons une surcouche
par-dessus `django-ninja`, le système de permissions de django
et notre propre système.
Cette dernière est documentée [ici](../perms.md).

### Incompatibilité avec certaines permissions

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

### CSRF

!!!info "A propos du csrf"

    Le [CSRF (*cross-site request forgery*)](https://fr.wikipedia.org/wiki/Cross-site_request_forgery)
    est un vecteur d'attaque sur le web consistant
    à soumettre des données au serveur à l'insu
    de l'utilisateur, en profitant de sa session.

    C'est une attaque qui peut se produire lorsque l'utilisateur
    est authentifié par cookie de session.
    En effet, les cookies sont joints automatiquement à
    toutes les requêtes ;
    en l'absence de protection contre le CSRF, 
    un attaquant parvenant à insérer un formulaire 
    dans la page de l'utilisateur serait en mesure
    de faire presque n'importe quoi en son nom,
    et ce sans même que l'utilisateur ni les administrateurs
    ne s'en rendent compte avant qu'il ne soit largement trop tard !

    Sur le CSRF et les moyens de s'en prémunir, voir :

    - [https://owasp.org/www-community/attacks/csrf]()
    - [https://security.stackexchange.com/questions/166724/should-i-use-csrf-protection-on-rest-api-endpoints]()
    - [https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html]()
    
Le CSRF, c'est dangereux.
Heureusement, Django vient encore une fois à notre aide,
avec des mécanismes intégrés pour s'en protéger.
Ceux-ci incluent notamment un système de 
[token CSRF](https://docs.djangoproject.com/fr/stable/ref/csrf/)
à fournir dans les requêtes POST/PUT/PATCH.

Ceux-ci sont bien adaptés au cycle requêtes/réponses
typiques de l'expérience utilisateur sur un navigateur, 
où les requêtes POST sont toujours effectuées après une requête
GET au cours de laquelle on a pu récupérer un token csrf.
Cependant, ils sont également gênants et moins utiles
dans le cadre d'une API REST, étant donné
que l'authentification cesse d'être implicite :
la clef d'API doit être explicitement jointe aux headers,
pour chaque requête.

Pour ces raisons, la vérification CSRF ne prend place
que pour la vérification de l'authentification
par cookie de session.

!!!warning "L'ordre est important"

    Si vous écrivez le code suivant, l'authentification par clef d'API
    ne marchera plus :
    
    ```python
    @api_controller("/foo")
    class FooController(ControllerBase):
        @route.post("/bar", auth=[SessionAuth(), ApiKeyAuth()])
        def post_bar(self, club_id: int): ...
    ```
    
    En effet, la vérification du cookie de session intègrera
    toujours la vérification CSRF.
    Or, un échec de cette dernière est traduit par django en un code HTTP 403
    au lieu d'un HTTP 401.
    L'authentification se retrouve alors court-circuitée,
    faisant que la vérification de la clef d'API ne sera jamais appelée.
    
    `SessionAuth` doit donc être déclaré **après** `ApiKeyAuth`.

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
