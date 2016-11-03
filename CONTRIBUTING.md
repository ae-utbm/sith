*Contribuer c'est la vie*
=========================

Hey ! Tu veux devenir un mec bien et en plus devenir bon en python si tu l'es pas déjà ?
Il se trouve que le sith AE prévu pour l'été 2016 a besoin de toi !

Pour faire le sith, on utilise le framework Web [Django](https://docs.djangoproject.com/fr/1.8/intro/)
N'hésite pas à lire les tutos et à nous demander (ae.info@utbm.fr).

Bon, passons aux choses sérieuses, pour bidouiller le sith sans le casser :
Ben en fait, tu peux pas le casser, tu vas juste t'amuser comme un petit fou sur un clone du sith.

C'est pas compliqué, il suffit d'avoir [Git](http://www.git-scm.com/book/fr/v2), python et pip (pour faciliter la gestion des paquets python).

Tout d'abord, tu vas avoir besoin d'un compte Gitlab pour pouvoir te connecter.
Ensuite, tu fais :
`git clone https://ae-dev.utbm.fr/ae/Sith.git`
Avec cette commande, tu clones le sith AE dans le dossier courant.

    cd Sith
    virtualenv --clear --python=python3 env_sith`
    source env_sith/bin/activate
    pip install -r requirements.txt

Maintenant, faut passer le sith en mode debug dans le fichier de settings personnalisé.

    cat "DEBUG=True" > sith/settings_custom.py
    cat 'SITH_URL = "localhost:8000"'% >> sith/settings_custom.py

Enfin, il s'aggit de créer la base de donnée de test

   ./manage.py setup
   répondre no

Et pour lancer le sith, tu fais `python3 manage.py runserver`

Voilà, c'est le sith AE. Il y a des issues dans le gitlab qui sont à régler. Si tu as un domaine qui t'intéresse, une appli que tu voudrais développer, n'hésites pas et contacte-nous.
Va, et que l'AE soit avec toi.

Sites et doc cools
------------------

[Classy Class-Based Views](http://ccbv.co.uk/projects/Django/1.8/)
