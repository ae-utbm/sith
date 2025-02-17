## Dépendances du système

Certaines dépendances sont nécessaires niveau système :

- uv
- libssl
- libjpeg
- zlib1g-dev
- gettext
- redis

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

        Installez les dépendances :
        
        ```bash
        sudo apt install curl build-essential libssl-dev \
            libjpeg-dev zlib1g-dev npm libffi-dev pkg-config \
            gettext git redis
        curl -LsSf https://astral.sh/uv/install.sh | sh
        ```

    === "Arch Linux"
    
        ```bash
        sudo pacman -Syu  # on s'assure que les dépôts et le système sont à jour

        sudo pacman -S uv gcc git gettext pkgconf npm redis
        ```

=== "macOS"

    Pour installer les dépendances, il est fortement recommandé d'installer le gestionnaire de paquets `homebrew <https://brew.sh/index_fr>`_.  
    Il est également nécessaire d'avoir installé xcode
    
    ```bash    
    brew install git uv npm redis
    
    # Pour bien configurer gettext
    brew link gettext # (suivez bien les instructions supplémentaires affichées)
    ```
    
    !!!note
    
        Si vous rencontrez des erreurs lors de votre configuration, n'hésitez pas à vérifier l'état de votre installation homebrew avec :code:`brew doctor`

!!!note

    Python ne fait pas parti des dépendances puisqu'il est automatiquement
    installé par uv.


## Finaliser l'installation

Clonez le projet (depuis votre console WSL, si vous utilisez WSL)
et installez les dépendances :

```bash
git clone https://github.com/ae-utbm/sith.git
cd sith

# Création de l'environnement et installation des dépendances
uv sync
npm install # Dépendances frontend
uv run ./manage.py install_xapian
```

!!!note

    La commande `install_xapian` est longue et affiche beaucoup
    de texte à l'écran.
    C'est normal, il ne faut pas avoir peur.

Une fois les dépendances installées, il faut encore
mettre en place quelques éléments de configuration,
qui peuvent varier d'un environnement à l'autre.
Ces variables sont stockées dans un fichier `.env`.
Pour le créer, vous pouvez copier le fichier `.env.example` :

```bash
cp .env.example .env
```

Les variables par défaut contenues dans le fichier `.env`
devraient convenir pour le développement, sans modification.

Maintenant que les dépendances sont installées
et la configuration remplie, nous allons pouvoir générer
des données utiles pendant le développement.

Pour cela, lancez les commandes suivantes :

```bash
# Prépare la base de données
uv run ./manage.py setup

# Installe les traductions
uv run ./manage.py compilemessages
```

!!!note

    Pour éviter d'avoir à utiliser la commande `uv run`
    systématiquement, il est possible de consulter [direnv](../howto/direnv.md).

## Démarrer le serveur de développement

Il faut toujours avoir préalablement activé 
l'environnement virtuel comme fait plus haut 
et se placer à la racine du projet.
Il suffit ensuite d'utiliser cette commande :

```bash
uv run ./manage.py runserver
```

!!!note

    Le serveur est alors accessible à l'adresse
    [http://localhost:8000](http://localhost:8000) 
    ou bien [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

!!!note

    Le serveur de développement se charge de lancer redis
    et les autres services nécessaires au bon fonctionnement du site.

!!!tip

    Vous trouverez également, à l'adresse
    [http://localhost:8000/api/docs](http://localhost:8000/api/docs),
    une interface swagger, avec toutes les routes de l'API.

!!! question "Pourquoi l'installation est aussi complexe ?"

    Cette question nous a été posée de nombreuses fois par des personnes
    essayant d'installer le projet.
    Il y a en effet un certain nombre d'étapes à suivre,
    de paquets à installer et de commandes à exécuter.
    
    Le processus d'installation peut donc sembler complexe.

    En réalité, il est difficile de faire plus simple.
    En effet, un site web a besoin de beaucoup de composants
    pour être développé : il lui faut au minimum
    une base de données, un cache, un bundler Javascript
    et un interpréteur pour le code du serveur.
    Pour nos besoin particuliers, nous utilisons également
    un moteur de recherche full-text.
    
    Nous avons tenté au maximum de limiter le nombre de dépendances
    et de sélecionner les plus simples à installer.
    Cependant, il est impossible de retirer l'intégralité
    de la complexité du processus.
    Si vous rencontrez des difficulté lors de l'installation,
    n'hésitez pas à demander de l'aide.

## Générer la documentation

La documentation est automatiquement mise en ligne à chaque envoi de code sur GitHub.
Pour l'utiliser en local ou globalement pour la modifier,
il existe une commande du site qui génère 
la documentation et lance un serveur la rendant
accessible à l'adresse [http://localhost:8080](http://localhost:8000).
Cette commande génère la documentation à 
chacune de ses modifications,
inutile de relancer le serveur à chaque fois.

```bash
uv run mkdocs serve
```

## Lancer les tests

Pour lancer les tests, il suffit d'utiliser 
la commande suivante :

```bash
# Lancer tous les tests
uv run pytest

# Lancer les tests de l'application core
uv run pytest core

# Lancer les tests de la classe UserRegistrationTest de core
uv run pytest core/tests/tests_core.py::TestUserRegistration
```

!!!note

    Certains tests sont un peu longs à tourner.
    Pour ne faire tourner que les tests les plus rapides,
    vous pouvez exécutez pytest ainsi :

    ```bash
    uv run pytest -m "not slow"

    # vous pouvez toujours faire comme au-dessus
    uv run pytest core -m "not slow"
    ```

    A l'inverse, vous pouvez ne faire tourner que les tests
    lents en remplaçant `-m "not slow"` par `-m slow`.

    De cette manière, votre processus de développement
    devrait être un peu plus fluide.
    Cependant, n'oubliez pas de bien faire tourner
    tous les tests avant de push un commit.


