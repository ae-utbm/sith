Le versioning
=============

Dans le monde du développement, nous faisons face à un problème relativement étrange pour un domaine aussi avancé : on est brouillon.

On teste, on envoie, ça marche pas, on reteste, c'est ok. Par contre, on a oublié plein d'exceptions. Et on refactor. Ça marche mieux mais c'est moins rapide, etc.

Et derrière tout ça, on fait des trucs qui marchent puis on se retrouve dans la mouise parce qu'on a effacé un morceau de code qui nous aurait servi plus tard.

Pour pallier ce problème, le programmeur a créé un principe révolutionnaire (ouais... à mon avis, on s'est inspiré d'autres trucs, mais on va dire que c'est nous les créateurs) : le Versioning (*Apparition inexpliquée*).

D'après projet-isika (c'est pas wikipedia ouais, ils étaient pas clairs eux), le versioning (ou versionnage en français mais c'est quand même vachement dégueu comme mot) consiste à travailler directement sur le code source d'un projet, en gardant toutes les versions précédentes. Les outils du versioning aident les développeurs à travailler parallèlement sur différentes parties du projet et à revenir facilement aux étapes précédentes de leur travail en cas de besoin. L’utilisation d’un logiciel de versioning est devenue quasi-indispensable pour tout développeur, même s’il travaille seul.

Un versioning pour les gouverner tous
-------------------------------------

On va vite fait passer sur les différents logiciels de contrôle de version avant de revenir à l'essentiel, le vrai, le beau, l'unique et l'ultime : Git.

**Source Code Control System (SCCS)**) : Développé en 1972 dans les labos d'IBM, il a été porté sur Unix pour ensuite donner naissance à RCS.
**GNU RCS (Revision Control System)** : RCS est à l'origine un projet universitaire, initié au début des années 1980, et maintenu pendant plus d'une décennie par Walter F. Tichy au sein de l'université Purdue.

Ce logiciel représente à l'époque une alternative libre au système SCCS, et une évolution technique, notamment par son interface utilisateur, plus conviviale, et une récupération des données, plus rapide, par l'amélioration du stockage des différentes versions. Ce gain de performance provient d'un algorithme appelé en anglais « reverse differences » (ou plus simplement « deltas ») et consiste à stocker la copie complète des versions les plus récentes et conserver uniquement les changements réalisés.

**CVS (Concurrent Versions System)** : En gros, c'est la première fois qu'on essaie de fusionner des versions *concurrentes* (dis-donc, quel hasard que ce soit des concurrents vu le nom du système !) de fichiers sources. C'était pas forcément compliqué : en gros, il y avait un serveur qui prenait à chaque fois la dernière version de chaque fichier, les développeurs devaient toujours avoir la dernière version du fichier s'ils voulaient éditer celui-ci. Si c'était pas le cas, le serveur les envoyait paitre.

**SVN (Subversion)** : En gros, c'est comme CVS mais avec quelques améliorations du fait du refactoring complet fait par Apache. Subversion permet notamment le renommage et le déplacement de fichiers ou de répertoires sans en perdre l'historique. On a aussi un versioning sur les metadatas (genre les changements de permissions des fichiers.

**Git** : Enfin le voilà. Le versioning ultime. Créé par Linus Torvalds en 2005, il permet notamment au bordel qu'est Linux d'être maintenu par des développeurs du monde entier grâce à un système original de version : en gros, chaque ordinateur a une version du code source et il n'y a pas forcément un serveur central qui garde tout (et demande un compte à chaque fois. Bon, maintenant on est de retour au format minitel avec Github mais on va vous montrer comment s'en sortir). Il y a également un système de branche pour pouvoir gérer différentes versions du code en parallèle. Tout est fait sous forme de petits fichiers de versioning qui vont faire des copies des fichiers correspondant à la modification proposée. Bref, c'est trop bien et on a pas fait mieux.

C'est pas forcément utile de comprendre le fonctionnement interne de Git pour développer (la preuve, je n'ai pas franchement chercher au tréfond du bousin) mais c'est en revanche indispensable de comprendre comment l'utiliser avant de faire n'importe quoi. Du coup, on va voir ci-dessous comment utiliser Git et comment on l'utilise sur le site AE.

TLDR
----

Un système de versioning permet de faire de la merde dans votre code et de pouvoir revenir en arrière malgré tout. Ça permet aussi de coder à plusieurs.
Git est le meilleur système de gestion de version (ou système de versioning) que vous pourrez trouver à l'heure actuelle. Utilisez-le.