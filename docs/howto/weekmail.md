Le site est capable de générer des mails automatiques
contenant l’agrégation d'articles écrits par les administrateurs de clubs.
Le contenu est inséré dans un template standardisé
et contrôlé directement dans le code.
Il arrive régulièrement que l'équipe communication souhaite modifier ce template.
Que ce soient les couleurs,
l'agencement ou encore la bannière ou le footer,
voici tout ce qu'il y a à savoir sur le fonctionnement
du weekmail en commençant par la classe qui le contrôle.

## Modifier la bannière et le footer

Ces éléments sont contrôlés par les méthodes `get_banner` et `get_footer`
de la classe `Weekmail`. 
Les modifier est donc très simple,
il suffit de modifier le contenu de la fonction et
de rajouter les nouvelles images dans les statics.

Les images sont à ajouter dans `core/static/com/img`
et sont à nommer selon le type (banner ou footer), le semestre (Automne ou Printemps) et l'année.
Exemple : `weekmail_bannerA18.jpg` pour la bannière de l'automne 2018.

```python
from django.conf import settings
from django.templatetags.static import static

# Sélectionnez le fichier de bannière pour le weekmail de l'automne 2018

def get_banner(self):
    return "http://" + settings.SITH_URL + static("com/img/weekmail_bannerA18.jpg")
```

!!!note

    Penser à prendre les images au format **jpg** et à les compresser un peu,
    pour qu'elles soient le plus léger possible, 
    c'est bien mieux pour l'utilisateur final.

!!!warning

    Pensez à laisser les anciennes images dans le dossier 
    pour que les anciens weekmails ne soient pas affectés par les changements.

## Modifier le template

Il existe deux templates différents :

- Un en texte pur, qui sert pour le rendu dégradé des lecteurs
  de mails ne supportant pas le HTML
- un qui fait du rendu html.

Ces deux templates sont respectivement accessibles aux emplacements suivants :

- `com/templates/com/weekmail_renderer_html.jinja`
- `com/templates/com/weekmail_renderer_text.jinja`

!!!note

    Pour le rendu HTML, pensez à utiliser le CSS et le javascript 
    le plus simple possible pour que le rendu se fasse correctement
    dans les clients mails qui sont souvent capricieux.

!!!note

    Le CSS est inclus statiquement pour que toute modification 
    ultérieure de celui-ci n'affecte pas les versions précédemment envoyées.

!!!warning

    Si vous souhaitez ajouter du contenu,
    n'oubliez pas de bien inclure ce contenu dans les deux templates.
