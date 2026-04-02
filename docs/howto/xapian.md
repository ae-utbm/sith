## Pourquoi Xapian

Xapian permet de faire de la recherche fulltext.
C'est une librairie écrite en C++ avec des bindings Python 
qu'on utilise avec la dépendance `django-haystack` via `xapian-haystack`.

Elle a les avantages suivants:

* C'est très rapide et ça correspond très bien à notre échelle
* C'est performant
* Pas besoin de service supplémentaire, c'est une librairie qui utilise des fichiers, comme sqlite

Mais elle a un défaut majeur: on ne peut pas « juste » la `pip install`, 
il faut installer une librairie système et des bindings et ça a toujours été 
l'étape la plus frustrante et buggée de notre process d'installation. C'est 
aussi la seule raison qui fait que le projet n'es pas compatible windows.

## Mettre à jour Xapian

Pour installer xapian le plus simplement possible, on le compile depuis les 
sources via la commande `./manage.py install_xapian` comme indiqué dans la 
documentation d'installation.

La version de xapian est contrôllée par le `pyproject.toml` dans la section 
`[tool.xapian]`.

Cette section ressemble à ceci:

```toml
[tool.xapian]
version = "x.y.z"
core-sha256 = "abcdefghijklmnopqrstuvwyz0123456789"
bindings-sha256 = "abcdefghijklmnopqrstuvwyz0123456789"
```

Comme on peut le voir, il y a 3 variables différentes, une variable de version, 
qui sert à choisir la version à télécharger, et deux variables sha256.

Ces variables sha256 permettent de protéger des attaques par supply chain, un 
peu comme uv et npm font avec leurs respectifs `uv.lock` et `package-lock.json`
. Elles permettent de vérifier que les fichiers téléchargés n'ont pas été 
altérés entre la configuration du fichier et l'installation par l'utilisateur 
et/ou le déploiement.

L'installation de xapian passe par deux fichiers, `xapian-core` et 
`xapian-bindings` disponnibles sur [https://xapian.org/download](https://xapian.org/download).

Lorsque le script d'installation télécharge les fichiers, il vérifie leur 
signature sha256 contre celles contenues dans ces deux variables. Si la 
signature n'es pas la même, une erreur est levée, protégant l'utilisateur 
d'une potentielle attaque.

Pour mettre à jour, il faut donc changer la version ET modifier la signature !

Pour récupérer ces signatures, il suffit de télécharger soi même les archives 
du logiciel sur ce site, utiliser la commande `sha256sum` dessus et, enfin, 
reporter la valeur sortie par cette commande.

Pour ce qui est de la correspondance, `core-sha256` correspond à la signature 
de `xapian-core` et `bindings-sha256` de `xapian-bindings`.

Voici un bout de script qui peut faciliter une mise à jour:

```bash
VERSION="x.y.z" # À modifier avec la bonne version
curl -O "https://oligarchy.co.uk/xapian/${VERSION}/xapian-core-${VERSION}.tar.xz"
sha256sum xapian-core-${VERSION}.tar.xz # Affiche la signature pour `core-sha256`
rm -f xapian-core-${VERSION}

curl -O "https://oligarchy.co.uk/xapian/${VERSION}/xapian-bindings-${VERSION}.tar.xz"
sha256sum xapian-bindings-${VERSION}.tar.xz # Affiche la signature pour `bindingse-sha256`
rm -f xapian-bindings-${VERSION}.tar.xz
```