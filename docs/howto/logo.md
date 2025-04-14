## Les logos de promo

Une fois par an, il est généralement nécessaire d'ajouter le
nouveau logo d'une promo. C'est un processus manuel.

!!!note "Automatisation"

	Créer une interface automatique sur le site serait compliqué
	et long à faire. Les erreurs de format des utilisateurs sont
	généralement nombreuses et on se retrouverais souvent avec
	des logos ratatinés. Il est donc plus simple et plus fiable
	de faire cette opération manuellement, ça prend quelques
	minutes et on est certain de la qualité à la fin.

### avec une commande django
```bash
./manage.py add_promo_logo numero_de_promo chemin_dacces_du_logo
```
options:

* `--force/-f` pour automatiquement écraser les logos de promo avec le même nom.

### manuellement
Les logos de promo sont à manuellement ajouter dans le projet.
Ils se situent dans le dossier `core/static/core/img/`.

Leur format est le suivant:

* PNG à fond transparent
* Taille 120x120 px
* Nom `promo_xx.png`
