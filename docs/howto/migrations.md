## Qu'est-ce qu'une migration ?

Une migration est un fichier Python qui contient
des instructions pour modifier la base de données.
Une base de données évolue au cours du temps,
et les migrations permettent de garder une trace
de ces modifications.

Grâce à elles, on peut également apporter des modifications
à la base de données sans être obligées de la recréer.
On applique seulement les modifications nécessaires.

## Appliquer les migrations

Pour appliquer les migrations, exécutez la commande suivante :

```bash
python ./manage.py migrate
```

Vous remarquerez peut-être que cette commande
a été utilisée dans la section 
[Installation](../tutorial/install.md).
En effet, en partant d'une base de données vierge
et en appliquant toutes les migrations, on arrive
à l'état actuel de la base de données. 
Logique.

Si vous utilisez cette commande sur une base de données
sur laquelle toutes les migrations ont été appliquées,
elle ne fera rien.

Si vous utilisez cette commande sur une base de données
sur laquelle seule une partie des migrations ont été appliquées,
seules les migrations manquantes seront appliquées.

## Créer une migration

Pour créer une migration, exécutez la commande suivante :

```bash
python ./manage.py makemigrations
```

Cette commande comparera automatiquement le contenu
des classes de modèles et le comparera avec les
migrations déjà appliquées.
A partir de cette comparaison, elle générera
automatiquement une nouvelle migration.

!!! note

    La commande `makemigrations` ne fait que
    générer les fichiers de migration.
    Elle ne modifie pas la base de données.
    Pour appliquer la migration, n'oubliez pas la
    commande `migrate`.

Un fichier de migration ressemble à ça : 

```python
from django.db import migrations

    
class Migration(migrations.Migration):

    dependencies = [
        # liste des autres migrations à appliquer avant celle-ci
    ]

    operations = [
        # liste des opérations à appliquer sur la db
    ]
```

Grâce à la liste des dépendances, Django sait dans
quel ordre les migrations doivent être appliquées.
Grâce à la liste des opérations, Django sait quelles
sont les opérations à appliquer durant cette migration.

## Revenir à une migration antérieure

Lorsque vous développez, il peut arriver que vous vouliez
revenir à une migration antérieure.
Pour cela, il suffit d'appliquer la commande `migrate`
en spécifiant le nom de la migration à laquelle vous
voulez revenir :

```bash
python ./manage.py migrate <application> <numéro de la migration>
```

Par exemple, si vous voulez revenir à la migration `0001_initial` 
de l'application `customer`, vous pouvez exécuter la commande suivante :

```bash
python ./manage.py migrate customer 0001
```

## Customiser une migration

Il peut arriver que vous ayez besoin de modifier
le fichier de migration généré par Django.
Par exemple, si vous voulez exécuter un script Python
lors de l'application de la migration.

Dans ce cas, vous pouvez trouver les fichiers de migration
dans le dossier `migrations` de chaque application.
Vous pouvez modifier le fichier Python correspondant
à la migration que vous voulez modifier.

Ajoutez l'opération que vous voulez effectuer
dans l'attribut `operations` de la classe `Migration`.

Par exemple :

```python
from django.db import migrations

def forwards_func(apps, schema_editor):
    print("Appplication de la migration")

def reverse_func(apps, schema_editor):
    print("Annulation de la migration")
    
class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
```

!!! warning "Script d'annulation de la migration"

    Lorsque vous incluez un script Python dans une migration,
    incluez toujours aussi un script d'annulation,
    sinon Django ne pourra pas annuler la migration
    après son application.

    Vous ne pourrez donc pas revenir à un état antérieur
    de la db, à moins de la recréer de zéro.

## Fusionner des migrations

Quand on travaille sur une fonctionnalité
qui nécessite une modification de la base de données,
les fichiers de migration sont comme toute chose :
on peut se rendre compte que les changements
apportés pourraient être meilleurs.

Par exemple, supposons que nous voulons créer un modèle
représentant une UE suivie par un étudiant
(ne demandez pas pourquoi on voudrait faire ça, 
c'est juste pour l'exemple).
Un tel modèle aurait besoin des informations suivantes :

- l'utilisateur
- le code de l'UE

On écrirait donc, dans l'application `pedagogy` :
```python
from django.db import models
from core.models import User

class UserUe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ue = models.CharField(max_length=10)
```

Et nous aurions le fichier de migration suivant : 
```python
from django.db import migrations, models
from django.conf import settings

class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("pedagogy", "0003_alter_uv_language"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserUe",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("ue", models.CharField(max_length=10)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
```


On finit son travail, on soumet la PR.
Mais là, quelqu'un fait remarquer qu'il existe déjà
un modèle pour représenter une UE.
On modifie donc le modèle :

```python
from django.db import models
from core.models import User
from pedagogy.models import UV

class UserUe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ue = models.ForeignKey(UV, on_delete=models.CASCADE)
```

On refait la commande `makemigrations` et on obtient :
```python
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("pedagogy", "0004_userue"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userue",
            name="ue",
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE, to="pedagogy.uv"
            ),
        ),
    ]
```

Sauf que maintenant, nous avons deux fichiers de migration,
alors qu'en réalité, on ne souhaite faire qu'une seule migration,
une fois qu'on aura expédié le code en prod.
Certes, ça fonctionnerait d'appliquer les deux, mais ça pose
un problème d'encombrement.

Plus il y a de fichiers de migrations, plus il y a de migrations
à résoudre au moment de l'installation du projet chez quelqu'un,
plus c'est embêtant à gérer et plus Django prendra du temps
à résoudre les migrations.

C'est pourquoi il est bon de respecter le principe :
une PR = un fichier de migration maximum par application.

Nous voulons donc fusionner les deux, pour n'en garder qu'une.
Pour ça, deux manières de procéder :

- le faire à la main
- utiliser la commande squashmigrations

Pour la méthode manuelle, on ne pourrait pas vous dire exhaustivement
comment faire.
Mais ne vous inquiétez pas, ce n'est pas très dur.
Regardez bien quelles sont les instructions utilisées par django
pour les opérations de migrations,
et avec un peu d'astuce et quelques copier-coller,
vous vous en sortirez comme des chefs.

Pour la méthode `squashmigrations`, exécutez la commande 

```bash
python ./manage.py squasmigrations <app> <migration de début (incluse)> <migration de fin (incluse)> 
```

Par exemple, dans notre cas, ça donnera :

```bash
python ./manage.py squasmigrations pedagogy 0004 0005 
```

La commande vous donnera ceci :
```python
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):
    replaces = [("pedagogy", "0004_userue"), ("pedagogy", "0005_alter_userue_ue")]

    dependencies = [
        ("pedagogy", "0003_alter_uv_language"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserUe",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "ue",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE, to="pedagogy.uv"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
```

Vous pouvez alors supprimer les deux autres fichiers.

Vous remarquerez peut-être la présence de la ligne suivante :
```python
replaces = [("pedagogy", "0004_userue"), ("pedagogy", "0005_alter_userue_ue")]
```

Cela sert à dire que cette migration doit être appliquée
à la place des deux autres.
Une fois que vous aurez supprimé les deux fichiers,
supprimez également cette ligne.

!!!warning

    Django sait quelles migrations ont été appliquées,
    en les stockant dans une table de la db.
    Si une migration est enregistrée en db, sans que le fichier
    de migration correspondant existe,
    la commande `migrate` échoue.

    Quand vous faites un `squashmigrations`,
    pensez donc à appliquer la commande `migrate`
    juste après (mais avant la suppression des anciens fichiers),
    pour que Django supprime de la base de données
    les migrations devenues inutiles.
