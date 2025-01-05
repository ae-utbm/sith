Le code du site est entièrement écrit en anglais, 
le texte affiché aux utilisateurs l'est également. 
La traduction en français se fait 
ultérieurement avec un fichier de traduction.
Voici un petit guide rapide pour apprendre à s'en servir.

## Dans le code du logiciel

Imaginons que nous souhaitons afficher "Hello"
et le traduire en français.
Voici comment signaler que ce mot doit être traduit.

Si le mot est dans le code Python :

```python
from django.utils.translation import gettext as _

help_text=_("Hello")
```

Si le mot apparaît dans le template Jinja :

```jinja
{% trans %}Hello{% endtrans %}
```

Si on est dans un fichier javascript ou typescript :

```js
gettext("Hello");
```

## Générer le fichier django.po

La traduction se fait en trois étapes. 
Il faut d'abord générer un fichier de traductions,
l'éditer et enfin le compiler au format binaire pour qu'il soit lu par le serveur.

```bash
# Pour le backend
./manage.py makemessages \
  --locale=fr \
  -e py,jinja \
  --ignore=node_modules \
  --add-location=file 

# Pour le frontend
./manage.py makemessages \
  --locale=fr \
  -d djangojs \
  -e js,ts \
  --ignore=node_modules \
  --ignore=staticfiles/generated \
  --add-location=file
```

## Éditer le fichier django.po

```locale
# locale/fr/LC_MESSAGES/django.po

# ...
msgid "Hello"
msgstr "" # Ligne à modifier

# ...
```

!!!note

	Si les commentaires suivants apparaissent, pensez à les supprimer.
    Ils peuvent gêner votre traduction.

	```
    #, fuzzy
    #| msgid "Bonjour"
    ```


## Générer le fichier django.mo

Il s'agit de la dernière étape.
Un fichier binaire est généré à partir du fichier django.mo.

```bash
./manage.py compilemessages
```

!!!tip

	Pensez à redémarrer le serveur si les traductions ne s'affichent pas