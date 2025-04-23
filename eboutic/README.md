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

- `EbouticMainView` (GET/POST) : la vue retournant la page principale de la boutique en ligne.
Cette vue effectue un filtrage des produits à montrer à l'utilisateur en
fonction de ce qu'il a le droit d'acheter.
Elle est en charge de récupérer le formulaire de création d'un panier et
redirige alors vers la vue de checkout.
- ``payment_result`` (GET) : retourne une page assez simple disant à l'utilisateur
si son paiement a échoué ou réussi. Cette vue est appelée par redirection
lorsque l'utilisateur paye son panier avec son argent du compte AE.
- ``EbouticCheckout`` (GET/POST) : Page récapitulant le contenu d'un panier.
Permet de sélectionner le moyen de paiement et de mettre à jour ses coordonnées
de paiement par carte bancaire.
- ``PayWithSith`` (POST) : paie le panier avec l'argent présent sur le compte
AE. Redirige vers `payment_result`.
- ``ETransactionAutoAnswer`` (GET) : vue destinée à communiquer avec le service 
de paiement bancaire pour valider ou non le paiement de l'utilisateur.
- ``BillingInfoFormFragment`` (GET/POST) : vue destinée à gérer les informations de paiement de l'utilisateur courant.

# Les templates

- ``eboutic_payment_result.jinja`` : très court template contenant juste
un message pour dire à l'utilisateur si son achat s'est bien déroulé.
Retourné par la vue ``payment_result``.
- ``eboutic_checkout.jinja`` : template contenant un résumé du panier et deux
boutons, un pour payer avec le site AE et l'autre pour payer par carte bancaire.
Retourné par la vue ``EbouticCheckout``
- ``eboutic_billing_info.jinja`` : formulaire de modification des coordonnées bancaires.
Elle permet également de mettre à jour ses coordonnées de paiement
- ``eboutic_main.jinja`` : le plus gros template de cette application. Contient
une interface pour que l'utilisateur puisse consulter les produits et remplir
son panier. Les opérations de remplissage du panier se font entièrement côté client.
À chaque clic pour ajouter ou retirer un élément du panier, le script JS
  (AlpineJS, plus précisément) édite en même temps le localStorage du navigateur. 
Cette vue fabrique dynamiquement un formulaire qui sera soumis au serveur.

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
