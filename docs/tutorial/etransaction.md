
## Fonctionnement général

La boutique en ligne nécessite une interaction
avec la banque pour son fonctionnement.

Malheureusement, la manière dont cette interaction marche
est trop complexe pour être résumée ici.

Nous ne pouvons donc que vous redirigez vers la doc du crédit
agricole : 
[https://www.ca-moncommerce.com/espace-client-mon-commerce/up2pay-e-transactions/ma-documentation/](https://www.ca-moncommerce.com/espace-client-mon-commerce/up2pay-e-transactions/ma-documentation/)

## Limite de clic et expiration des paniers

Certains produits peuvent avoir un quota de vente.
Une fois ce dernier atteint, il ne doit plus être possible de les acheter.

Pour éviter que cette limite soit dépassée si jamais plusieurs utilisateurs
commandent et achètent ce produit à peu près en même temps,
un produit est considéré comme « réservé » une fois placé dans un panier.
La création du panier s'effectue lors de la soumission du formulaire sur l'eboutic.
Une fois la transaction accomplie, le panier est supprimé.

Cependant, il reste un problème : 
que faire des utilisateurs qui créent un panier, mais ne terminent
pas la transaction ?
Pour résoudre ce cas, les paniers ont une durée de validité,
définie dans le `settings.py`, grâce à deux variables :

- `settings.SITH_EBOUTIC_BASKET_TIMEOUT` : 
  le temps pendant lequel un utilisateur peut payer avec son compte AE
  ou démarrer une etransaction
- `settings.SITH_EBOUTIC_ETRANSACTION_TIMEOUT` :
  le temps alloué à l'utilisateur pour effectuer une etransaction ;
  au-delà de cette durée, la banque refusera le paiement
  et notifiera le sith de l'erreur.

Une fois expiré le temps défini par 
`settings.SITH_EBOUTIC_BASKET_TIMEOUT + settings.SITH_EBOUTIC_ETRANSACTION_TIMEOUT`, 
les produits contenus dans le panier sont à nouveau 
disponibles à la vente.
