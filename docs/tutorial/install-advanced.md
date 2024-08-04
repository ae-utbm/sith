Si le projet marche chez vous après avoir suivi les étapes 
données dans la page précédente, alors vous pouvez développer.
Ce que nous nous vous avons présenté n'est absolument pas
la même configuration que celle du site, mais elle n'en
est pas moins fonctionnelle.

Cependant, vous pourriez avoir envie de faire en sorte
que votre environnement de développement soit encore plus
proche de celui en production.
Voici les étapes à suivre pour ça.

## Installer les dépendances manquantes

Pour installer complètement le projet, il va falloir
quelques dépendances en plus.
Commencez par installer les dépendances système :

=== "Linux"

    === "Debian/Ubuntu"

        ```bash
        sudo apt install postgresql redis libq-dev
        ```

    === "Arch Linux"
    
        ```bash
        sudo pacman -S postgresql redis
        ```

=== "macOS"

    ```bash
    brew install postgresql redis nginx lipbq
    export PATH="/usr/local/opt/libpq/bin:$PATH"
    source ~/.zshrc
    ```

Puis, installez les dépendances poetry nécessaires en prod :

```bash
poetry install --with prod
```

!!! info

    Certaines dépendances peuvent être un peu longues à installer
    (notamment psycopg-c).
    C'est parce que ces dépendances compilent certains modules
    à l'installation.

## Configurer Redis

Redis est utilisé comme cache.
Assurez-vous qu'il tourne :

```bash
sudo systemctl redis status
```

Et s'il ne tourne pas, démarrez-le :

```bash
sudo systemctl start redis
sudo systemctl enable redis  # si vous voulez que redis démarre automatiquement au boot
```

Puis ajoutez le code suivant à la fin de votre fichier
`settings_custom.py` :

```python
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379",
    }
}
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

Puis ajoutez le code suivant à la fin de votre
`settings_custom.py` :

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "sith",
        "USER": "sith",
        "PASSWORD": "password",
        "HOST": "localhost",
        "PORT": "",  # laissez ce champ vide pour que le choix du port soit automatique
    }
}
```

Enfin, créez vos données :

```bash
poetry run ./manage.py populate
```

!!! note

    N'oubliez de quitter la session de l'utilisateur
    postgres après avoir configuré la db.


## Mettre à jour la base de données antispam

L'anti spam nécessite d'être à jour par rapport à des bases de données externes.
Il existe une commande pour ça qu'il faut lancer régulièrement.
Lors de la mise en production, il est judicieux de configurer
un cron pour la mettre à jour au moins une fois par jour.

```bash
python manage.py update_spam_database
```
