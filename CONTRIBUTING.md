*Contribuer c'est la vie*
=========================

Hey ! Tu veux devenir un mec bien et en plus devenir bon en python si tu l'es pas déjà ?
Il se trouve que le sith AE prévu pour l'été 2016 a besoin de toi !

Pour faire le sith, on utilise le framework Web [Django](https://docs.djangoproject.com/fr/1.11/intro/)  
N'hésite pas à lire les tutos et à nous demander (ae.info@utbm.fr).

Bon, passons aux choses sérieuses, pour bidouiller le sith sans le casser :  
Ben en fait, tu peux pas le casser, tu vas juste t'amuser comme un petit fou sur un clone du sith.

C'est pas compliqué, il suffit d'avoir [Git](http://www.git-scm.com/book/fr/v2), python et pip (pour faciliter la gestion des paquets python).

Tout d'abord, tu vas avoir besoin d'un compte Gitlab pour pouvoir te connecter.  
Ensuite, tu fais :
`git clone https://ae-dev.utbm.fr/ae/Sith.git`
Avec cette commande, tu clones le sith AE dans le dossier courant.

```bash
cd Sith
virtualenv --system-site-packages --python=python3 env_sith
source env_sith/bin/activate
pip install -r requirements.txt
```

Attention aux dépendances système, à voir dans le README.md

Maintenant, faut passer le sith en mode debug dans le fichier de settings personnalisé.

```bash
echo "DEBUG=True" > sith/settings_custom.py
echo 'EXTERNAL_RES = "False"' >> sith/settings_custom.py
echo 'SITH_URL = "localhost:8000"' >> sith/settings_custom.py
```

Enfin, il s'agit de créer la base de donnée de test lors de la première utilisation

```bash
./manage.py setup
```

Et pour lancer le sith, tu fais `python3 manage.py runserver`

Voilà, c'est le sith AE. Il y a des issues dans le gitlab qui sont à régler. Si tu as un domaine qui t'intéresse, une appli que tu voudrais développer, n'hésites pas et contacte-nous.
Va, et que l'AE soit avec toi.

# Black

Pour uniformiser le formattage du code nous utilisons [Black](https://github.com/ambv/black). Cela permet d'avoir le même codestyle et donc le codereview prend moins de temps. Tout étant dans le même format, il est plus facile pour chacun de comprendre le code de chacun ! Cela permet aussi d'éviter des erreurs (y parait 🤷‍♀️).

Installation de black:

```bash
pip install black
```

## Sous VsCode:
Attention, pour VsCode, Black doit être installé dans votre virtualenv !
Ajouter ces deux lignes dans les settings de VsCode

```json
{
    "python.formatting.provider": "black",
    "editor.formatOnSave": true
}
```

## Sous Sublime Text
Il faut installer le plugin [sublack](https://packagecontrol.io/packages/sublack) depuis Package Control.

Il suffit ensuite d'ajouter dans les settings du projet (ou en global)

```json
{
    "sublack.black_on_save": true
}
```

Si vous utilisez le plugin [anaconda](http://damnwidget.github.io/anaconda/), pensez à modifier les paramètres du linter pep8 pour éviter de recevoir des warnings dans le formatage de black

```json
{
    "pep8_ignore": [
      "E203",
      "E266",
      "E501",
      "W503"
    ]
}
```

Sites et doc cools
------------------

[Classy Class-Based Views](http://ccbv.co.uk/projects/Django/1.11/)

Helpers:

`./manage.py makemessages --ignore "env/*" -e py,jinja`

`for f in $(find . -name "*.py" ! -path "*migration*" ! -path "./env/*" ! -path "./doc/*"); do cat ./doc/header "$f" > /tmp/temp && mv /tmp/temp "$f"; done`




