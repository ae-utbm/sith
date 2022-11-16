Eboutic
=======

# Aperçu général

L'application eboutic contient les vues, les templates et les modèles
nécessaires pour le fonctionnement de la boutique en ligne.
L'utilisateur peut acheter des produits en ligne et payer soit 
par carte bancaire soit avec l'argent qu'il possède sur son compte AE.

On effectue ici une séparation entre plusieurs types de produits : 
- les recharges de compte (``Refilling``) qui permettent de rajouter de 
l'argent sur le compte. Un panier contenant un élément de ce type ne pourra être
payé que par carte bancaire.
- Les cotisations (``Subscription``) qui permettent à un utilisateur de cotiser
à l'AE. Seul un utilisateur ayant déjà été cotisant pourra acheter ce produit.
Les primo-cotisants doivent s'adresser directement à un membre du bureau.
- Les produits normaux (badges, écussons, billets pour les soirées...)

Les utilisateurs cotisants ne peuvent pas voir les produits des non-cotisants
et vice-versa. Ce n'est pas la manière la plus satisfaisante de procéder, mais
c'est celle qui touchait le moins aux tables déjà en place.
Les produits avec une limite d'âge ne seront pas visibles par les utilisateurs ayant
un âge inférieur.

Le comportement de cette application dépend directement de celui des applications
``core`` et ``counter``. Les modèles de l'application ``Subscription`` sont
également utilisés. N'hésitez donc pas à vous pencher sur le fonctionnement des modules
susnommés afin de comprendre comment celui-ci marche.

# Les vues

Cette application contient les vues suivantes : 

- `eboutic_main` (GET) : la vue retournant la page principale de la boutique en ligne.
Cette vue effectue un filtrage des produits à montrer à l'utilisateur en
fonction de ce qu'il a le droit d'acheter.
Si cette vue est appelée lors d'une redirection parce qu'une erreur 
est survenue au cours de la navigation sur la boutique, il est possible
de donner les messages d'erreur à donner à l'utilisateur dans la session 
avec la clef ``"errors"``.
- ``payment_result`` (GET) : retourne une page assez simple disant à l'utilisateur
si son paiement a échoué ou réussi. Cette vue est appelée par redirection
lorsque l'utilisateur paye son panier avec son argent du compte AE.
- ``EbouticCommand`` (POST) : traite la soumission d'un panier par l'utilisateur.
Lors de l'appel de cette vue, la requête doit contenir un cookie avec l'état
du panier à valider. Ce panier doit strictement être de la forme : 
```
[
  {"id": <int>, "name": <str>, "quantity": <int>, "unit_price": <float>},
  {"id": <int>, "name": <str>, "quantity": <int>, "unit_price": <float>},
  <etc.>
]
```
Si le panier est mal formaté ou contient des valeurs invalides, 
une redirection est faite vers `eboutic_main`.
- ``pay_with_sith`` (POST) : paie le panier avec l'argent présent sur le compte
AE. Redirige vers `payment_result`.
- ``ETransactionAutoAnswer`` (GET) : vue destinée à communiquer avec le service 
de paiement bancaire pour valider ou non le paiement de l'utilisateur.

# Les templates

- ``eboutic_payment_result.jinja`` : très court template contenant juste
un message pour dire à l'utilisateur si son achat s'est bien déroulé.
Retourné par la vue ``payment_result``.
- ``eboutic_makecommand.jinja`` : template contenant un résumé du panier et deux
boutons, un pour payer avec le site AE et l'autre pour payer par carte bancaire.
Retourné par la vue ``EbouticCommand``
- ``eboutic_main.jinja`` : le plus gros template de cette application. Contient
une interface pour que l'utilisateur puisse consulter les produits et remplir
son panier. Les opérations de remplissage du panier se font entièrement côté client.
À chaque clic pour ajouter ou retirer un élément du panier, le script JS
  (AlpineJS, plus précisément) édite en même temps un cookie. 
Au moment de la validation du panier, ce cookie est envoyé au serveur pour
vérifier que la commande est valide et payer.

# Les modèles

- ``Basket`` : représente le panier d'un utilisateur. Un objet ``Basket`` est créé
quand l'utilisateur soumet son panier et supprimé quand le paiement est validé.
Si le paiement n'est pas validé, le panier est conservé en base de données
afin d'avoir une trace si l'utilisateur a quand même été débité et qu'il n'a pas
reçu ses produits à cause d'une erreur de synchronisation.
- ``Invoice`` : Un peu comme un panier, mais pour quand une transaction
a été validée.
- ``AbstractBaseItem`` : modèle utilisé pour être hérité par ``BasketItem`` et ``InvoiceItem``.
Me demandez pas pourquoi ``product_id`` est un IntegerField plutôt qu'une clef étrangère,
moi aussi je trouve ça complètement con. 
Le prix unitaire est indiqué dans ce modèle même si ça fait une redondance avec le modèle
``Product`` afin de garder le prix que l'élément avait au moment de sa vente,
même si le prix du produit de base est modifié.
- ``BasketItem`` : représente un élément présent dans le panier de l'utilisateur.
- ``InvoiceItem`` : représente un élément vendu.
