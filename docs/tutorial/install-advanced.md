Si le projet marche chez vous après avoir suivi les étapes 
données dans la page précédente, alors vous pouvez développer.
Ce que nous nous vous avons présenté n'est absolument pas
la même configuration que celle du site, mais elle n'en
est pas moins fonctionnelle.

Cependant, vous pourriez avoir envie de faire en sorte
que votre environnement de développement soit encore plus
proche de celui en production.
Voici les étapes à suivre pour ça.

!!!tip

    Configurer les dépendances du projet
    peut demander beaucoup d'allers et retours entre
    votre répertoire projet et divers autres emplacements.

    Vous pouvez gagner du temps en déclarant un alias :

    === "bash/zsh"

        ```bash
        alias cdp="cd /repertoire/du/projet"
        ```

    === "nu"

        ```nu
        alias cdp = cd /repertoire/du/projet
        ```

    Chaque fois qu'on vous demandera de retourner au répertoire
    projet, vous aurez juste à faire :

    ```bash
    cdp
    ```

## Installer les dépendances manquantes

Pour installer complètement le projet, il va falloir
quelques dépendances en plus.
Commencez par installer les dépendances système :

=== "Linux"

    === "Debian/Ubuntu"

        ```bash
        sudo apt install postgresql libq-dev nginx
        ```

    === "Arch Linux"
    
        ```bash
        sudo pacman -S postgresql nginx
        ```

=== "macOS"

    ```bash
    brew install postgresql lipbq nginx
    export PATH="/usr/local/opt/libpq/bin:$PATH"
    source ~/.zshrc
    ```

Puis, installez les dépendances nécessaires en prod :

```bash
uv sync --group prod
```

!!! info

    Certaines dépendances peuvent être un peu longues à installer
    (notamment psycopg-c).
    C'est parce que ces dépendances compilent certains modules
    à l'installation.

## Désactiver Honcho

Honcho est utilisé en développement pour simplifier la gestion
des services externes (redis, vite et autres futures).

En mode production, il est nécessaire de le désactiver puisque normalement
tous ces services sont déjà configurés.

Pour désactiver Honcho il suffit de ne sélectionner aucun `PROCFILE_` dans la config.

```dotenv
PROCFILE_STATIC=
PROCFILE_SERVICE=
```

!!! note

    Si `PROCFILE_STATIC` est désactivé, la recompilation automatique
    des fichiers statiques ne se fait plus.
    Si vous en avez besoin et que vous travaillez sans `PROCFILE_STATIC`,
    vous devez ouvrir une autre fenêtre de votre terminal
    et lancer la commande `npm run serve`

## Configurer Redis en service externe

Redis est installé comme dépendance mais pas lancé par défaut.

En mode développement, le sith se charge de le démarrer mais
pas en production !

Il faut donc lancer le service comme ceci:

```bash
sudo systemctl start redis
sudo systemctl enable redis  # si vous voulez que redis démarre automatiquement au boot
```

Puis modifiez votre `.env` pour y configurer le bon port redis.
Le port du fichier d'exemple est un port non standard pour éviter
les conflits avec les instances de redis déjà en fonctionnement.

```dotenv
REDIS_PORT=6379
CACHE_URL=redis://127.0.0.1:${REDIS_PORT}/0
```

Si on souhaite configurer redis pour communiquer via un socket :

```dovenv
CACHE_URL=redis:///path/to/redis-server.sock
```

## Configurer PostgreSQL

PostgreSQL est utilisé comme base de données.

Passez sur le compte de l'utilisateur postgres 
et lancez l'invite de commande sql :

```bash
sudo su - postgres
psql
```

Puis configurez la base de données :

```postgresql
CREATE DATABASE sith;
CREATE USER sith WITH PASSWORD 'password';

ALTER ROLE sith SET client_encoding TO 'utf8';
ALTER ROLE sith SET default_transaction_isolation TO 'read committed';
ALTER ROLE sith SET timezone TO 'UTC';

GRANT ALL PRIVILEGES ON DATABASE sith TO SITH;
\q
```

Si vous utilisez une version de PostgreSQL supérieure ou égale
à 15, vous devez exécuter une commande en plus,
en étant connecté en tant que postgres :

```bash
psql -d sith -c "GRANT ALL PRIVILEGES ON SCHEMA public to sith";
```

Puis modifiez votre `.env`.
Dedans, décommentez l'url de la base de données
de postgres et commentez l'url de sqlite :

```dotenv
#DATABASE_URL=sqlite:///db.sqlite3
DATABASE_URL=postgres://sith:password@localhost:5432/sith
```

Enfin, créez vos données :

```bash
uv run ./manage.py setup
```

!!! note

    N'oubliez de quitter la session de l'utilisateur
    postgres après avoir configuré la db.

## Configurer nginx

Nginx est utilisé comme reverse-proxy.

!!!warning

    Nginx ne sert pas les fichiers de la même manière que Django.
    Les fichiers statiques servis seront ceux du dossier `/static`,
    tels que générés par les commandes `collectstatic` et
    `compilestatic`.
    Si vous changez du css ou du js sans faire tourner
    ces commandes, ces changements ne seront pas reflétés.

    De manière générale, utiliser nginx en dev n'est pas très utile,
    voire est gênant si vous travaillez sur le front.
    Ne vous embêtez pas avec ça, sauf par curiosité intellectuelle,
    ou bien si vous voulez tester spécifiquement 
    des interactions avec le reverse proxy.


Placez-vous dans le répertoire `/etc/nginx`, 
et créez les dossiers et fichiers nécessaires :

```bash
cd /etc/nginx/
sudo mkdir sites-enabled sites-available
sudo touch sites-available/sith.conf
sudo ln -s /etc/nginx/sites-available/sith.conf sites-enabled/sith.conf
```

Puis ouvrez le fichier `sites-available/sith.conf` et mettez-y le contenu suivant :

```nginx
server {
    listen 8000;

    server_name _;

    location /static/;
        root /repertoire/du/projet;
    }
    location ~ ^/data/(products|com|club_logos|upload)/ {
        root /repertoire/du/projet;
    }
    location ~ ^/data/(SAS|profiles|users|.compressed|.thumbnails)/ {
        # https://nginx.org/en/docs/http/ngx_http_core_module.html#internal
        internal;
        root /repertoire/du/projet;
    }

    location / {
        proxy_pass http://127.0.0.1:8001;
        include uwsgi_params;
    }
}
```

Ouvrez le fichier `nginx.conf`, et ajoutez la configuration suivante :

```nginx
http {
    # Toute la configuration
    # éventuellement déjà là

    include /etc/nginx/sites-enabled/sith.conf;
}
```

Vérifiez que votre configuration est bonne :

```bash
sudo nginx -t
```

Si votre configuration n'est pas bonne, corrigez-la.
Puis lancez ou relancez nginx :

```bash
sudo systemctl restart nginx
```

Dans votre `.env`, remplacez `SITH_DEBUG=true` par `SITH_DEBUG=false`.

Enfin, démarrez le serveur Django :

```bash
cd /repertoire/du/projet
uv run ./manage.py runserver 8001
```

Et c'est bon, votre reverse-proxy est prêt à tourner devant votre serveur.
Nginx écoutera sur le port 8000.
Toutes les requêtes vers des fichiers statiques et les medias publiques
seront servies directement par nginx.
Toutes les autres requêtes seront transmises au serveur django.

## Celery

Celery ne tourne pas dans django.
C'est une application à part, avec ses propres processus,
qui tourne de manière indépendante et qui ne communique
que par messages avec l'instance de django.

Pour faire tourner Celery, faites la commande suivante dans 
un terminal à part :

```bash
poetry run celery -A sith worker --beat -l INFO 
```


## Mettre à jour la base de données antispam

L'anti spam nécessite d'être à jour par rapport à des bases de données externes.
Il existe une commande pour ça qu'il faut lancer régulièrement.
Lors de la mise en production, il est judicieux de configurer
un cron pour la mettre à jour au moins une fois par jour.

```bash
python manage.py update_spam_database
```

## Personnaliser l'environnement

Le site utilise beaucoup de variables configurables via l'environnement.
Cependant, pour des raisons de maintenabilité et de simplicité
pour les nouveaux développeurs, nous n'avons mis dans le fichier
`.env.example` que celles qui peuvent nécessiter d'être fréquemment modifiées
(par exemple, l'url de connexion à la db, ou l'activation du mode debug).

Cependant, il en existe beaucoup d'autres, que vous pouvez trouver
dans le `settings.py` en recherchant `env.` 
(avec `grep` ou avec un ++ctrl+f++ dans votre éditeur).

Si le besoin de les modifier se présente, c'est chose possible.
Il suffit de rajouter la paire clef-valeur correspondante dans le `.env`.

!!!tip

    Si vous utilisez nushell, 
    vous pouvez automatiser le processus avec
    avec le script suivant, qui va parser le `settings.py`
    pour récupérer toutes les variables d'environnement qui ne sont pas
    définies dans le .env puis va les rajouter :

    ```nu
    # si le fichier .env n'existe pas, on le crée
    if not (".env" | path exists) {
        cp .env.example .env
    }
    
    # puis on récupère les variables d'environnement déjà existantes
    let existing = open .env 
    
    # on récupère toutes les variables d'environnement utilisées
    # dans le settings.py qui ne sont pas encore définies dans le .env,
    # on les convertit dans un format .env,
    # puis on les ajoute à la fin du .env
    let regex = '(env\.)(?<method>\w+)\(\s*"(?<env_name>\w+)"(\s*(, default=)(?<value>.+))?\s*\)';
    let content = open sith/settings.py;
    let vars = $content
        | parse --regex $regex 
        | filter { |i| $i.env_name not-in $existing }
        | each { |i|
            let parsed_value = match [$i.method, $i.value] {
                ["str", "None"] => ""
                ["bool", $val] => ($val | str downcase)
                ["list", $val] => ($val | str trim -c '[' | str trim -c ']')
                ["path", $val] => ($val | str replace 'BASE_DIR / "' $'"(pwd)/')
                [_, $val] => $val
            }
            $"($i.env_name)=($parsed_value)"
        }
    
    if ($vars | is-not-empty) {
        # on ajoute les nouvelles valeurs, 
        # en mettant une ligne vide de séparation avec les anciennes
        ["", ...$vars] | save --append .env
    }
    
    print $"($vars | length) values added to .env"
    ```