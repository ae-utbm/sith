## Dépendances du système

Certaines dépendances sont nécessaires niveau système :

- poetry
- libssl
- libjpeg
- zlib1g-dev
- python
- gettext

### Installer WSL

Si vous utilisez Windows, je suis navré
de vous annoncer que, certaines dépendances étant uniquement disponibles sur des sytèmes UNIX,
il n'est pas possible de développer le site sur ce système d'exploitation.

Heureusement, il existe une alternative qui ne requiert pas de désinstaller votre
OS ni de mettre un dual boot sur votre ordinateur : `WSL`.

- **Prérequis:** vous devez être sur Windows 10 version 2004 ou ultérieure (build 19041 & versions ultérieures) ou Windows 11.
- **Plus d'info:** [docs.microsoft.com](https://docs.microsoft.com/fr-fr/windows/wsl/install)

```shell
# dans un shell Windows
wsl --install

# afficher la liste des distribution disponible avec WSL
wsl -l -o

# installer WSL avec une distro (ubuntu conseillé)
wsl --install -d <nom_distro>
```

Une fois `WSL` installé, mettez à jour votre distribution et
installez les dépendances (voir la partie installation sous Ubuntu).

Pour accéder au contenu d'un répertoire externe à `WSL`,
il suffit d'utiliser la commande suivante :

```bash
# oui c'est beau, simple et efficace
cd /mnt/<la_lettre_du_disque>/vos/fichiers/comme/dhab
```

!!!note

    À ce stade, si vous avez réussi votre installation de `WSL` ou bien qu'il
    était déjà installé, vous pouvez effectuer la mise en place du projet en suivant
    les instructions pour votre distribution.

### Installer les dépendances

=== "Linux"

    === "Debian/Ubuntu"

        Avant toute chose, assurez-vous que votre système est à jour :
        
        ```bash
        sudo apt update
        sudo apt upgrade
        ```

        Puis, si ce n'est pas déjà fait, installez Python :    
        ```bash
        sudo apt install python3
        # on sait jamais
        sudo apt install python-is-python3
        ```
        Si vous utilisez Ubuntu 22.04 ou Ubuntu 24.04,
        votre version de Python devrait être compatible
        par défaut avec celle du projet.
        Si ce n'est pas le cas, nous vous conseillons
        d'utiliser [pyenv](https://github.com/pyenv/pyenv)

        Puis installez les autres dépendances :
        
        ```bash
        sudo apt install build-essential libssl-dev libjpeg-dev zlib1g-dev python-dev npm \
                 libffi-dev python-dev-is-python3 pkg-config \
                 gettext git pipx

        pipx install poetry
        ```

    === "Arch Linux"
    
        ```bash
        sudo pacman -Syu  # on s'assure que les dépôts et le système sont à jour

        sudo pacman -S python
        
        sudo pacman -S gcc git gettext pkgconf python-poetry npm
        ```

=== "macOS"

    Pour installer les dépendances, il est fortement recommandé d'installer le gestionnaire de paquets `homebrew <https://brew.sh/index_fr>`_.  
    Il est également nécessaire d'avoir installé xcode
    
    ```bash    
    brew install git python pipx npm
    pipx install poetry
    
    # Pour bien configurer gettext
    brew link gettext # (suivez bien les instructions supplémentaires affichées)
    ```
    
    !!!note
    
        Si vous rencontrez des erreurs lors de votre configuration, n'hésitez pas à vérifier l'état de votre installation homebrew avec :code:`brew doctor`


## Finaliser l'installation

Clonez le projet et installez les dépendances :

```bash
git clone https://github.com/ae-utbm/sith3.git
cd sith3

# Création de l'environnement et installation des dépendances
poetry install # Dépendances backend
npm install    # Dépendances frontend
poetry run ./manage.py install_xapian
```

!!!note

    La commande `install_xapian` est longue et affiche beaucoup
    de texte à l'écran.
    C'est normal, il ne faut pas avoir peur.

Maintenant que les dépendances sont installées, nous
allons créer la base de données, la remplir avec des données de test,
et compiler les traductions.
Cependant, avant de faire cela, il est nécessaire de modifier
la configuration pour signifier que nous sommes en mode développement.
Pour cela, nous allons créer un fichier `sith/settings_custom.py`
et l'utiliser pour surcharger les settings de base.

```bash
echo "DEBUG=True" > sith/settings_custom.py
echo 'SITH_URL = "localhost:8000"' >> sith/settings_custom.py
```

Enfin, nous pouvons lancer les commandes suivantes :

```bash
# Activation de l'environnement virtuel
poetry shell

# Prépare la base de données
python ./manage.py setup

# Installe les traductions
python ./manage.py compilemessages
```

!!!note

    Pour éviter d'avoir à utiliser la commande `poetry shell`
    systématiquement, il est possible de consulter [direnv](../howto/direnv.md).

## Démarrer le serveur de développement

Il faut toujours avoir préalablement activé 
l'environnement virtuel comme fait plus haut 
et se placer à la racine du projet.
Il suffit ensuite d'utiliser cette commande :

```bash
python manage.py runserver
```

!!!note

    Le serveur est alors accessible à l'adresse
    [http://localhost:8000](http://localhost:8000) 
    ou bien [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

!!!tip

    Vous trouverez également, à l'adresse
    [http://localhost:8000/api/docs](http://localhost:8000/api/docs),
    une interface swagger, avec toutes les routes de l'API.

## Générer la documentation

La documentation est automatiquement mise en ligne à chaque envoi de code sur GitHub.
Pour l'utiliser en local ou globalement pour la modifier,
il existe une commande du site qui génère 
la documentation et lance un serveur la rendant
accessible à l'adresse [http://localhost:8080](http://localhost:8000).
Cette commande génère la documentation à 
chacune de ses modifications,
inutile de relancer le serveur à chaque fois.

!!!note

    Les dépendances pour la documentation sont optionnelles.
    Avant de commencer à travailler sur la doc, il faut donc les installer
    avec la commande `poetry install --with docs`

```bash
mkdocs serve
```

## Lancer les tests

Pour lancer les tests, il suffit d'utiliser 
la commande suivante :

```bash
# Lancer tous les tests
pytest

# Lancer les tests de l'application core
pytest core

# Lancer les tests de la classe UserRegistrationTest de core
pytest core/tests/tests_core.py::TestUserRegistration
```

!!!note

    Certains tests sont un peu longs à tourner.
    Pour ne faire tourner que les tests les plus rapides,
    vous pouvez exécutez pytest ainsi :

    ```bash
    pytest -m "not slow"

    # vous pouvez toujours faire comme au-dessus
    pytest core -m "not slow"
    ```

    A l'inverse, vous pouvez ne faire tourner que les tests
    lents en remplaçant `-m "not slow"` par `-m slow`.

    De cette manière, votre processus de développement
    devrait être un peu plus fluide.
    Cependant, n'oubliez pas de bien faire tourner
    tous les tests avant de push un commit.



## Vérifier les dépendances Javascript

Une commande a été écrite pour vérifier les éventuelles mises
à jour à faire sur les librairies Javascript utilisées.
N'oubliez pas de mettre à jour à la fois le fichier
de la librairie, mais également sa version dans `sith/settings.py`.

```bash
# Vérifier les mises à jour
python manage.py check_front
```
