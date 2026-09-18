## syntaxe aemark

Le site AE utilise markdown pour le rendu de la plupart
des textes saisis par les utilisateurs.
Cependant, la syntaxe utilisée n'est pas celle officielle
telle que définie par John Gruber,
mais est basée sur [CommonMark](https://commonmark.org/),
avec quelques variations pour les usages particuliers du site AE.

Les deux principaux ajouts sont :

- Les urls commençant par `page://` sont modifiées pour commencer par `/page/`
- Des modificateurs de taille peuvent être indiqués directement dans la source
  d'une image

Les variations d'aemark sont documentées sur
[le site AE](https://ae.utbm.fr/page/Aide_sur_la_syntaxe/).

Le code est hébergé sur le dépôt Git [aemark](https://github.com/ae-utbm/ae-markdown).

## Utiliser aemark

Le code du parser aemark est écrit en Rust dans une librairie
indépendante, avec des bindings vers différents langages.
Les librairies mises à disposition exposent une seule fonction,
qui prend simplement du markdown en entrée et renvoie l'HTML correspondant.

Les librairies pour les différents langages sont toutes
basées sur le même code Rust.
La seule différence entre chacune tient uniquement dans la manière
d'intégrer ce code dans les bindings.
De cette manière, le comportement est assuré d'être le même
sur toutes les plateformes disponibles, avec en prime des performances
respectables.


=== ":simple-python: Python"

    ```python
    from aemark import markdown

    result = markdown("this is some *markdown text* with __formatting__")
    ```

=== ":simple-javascript: Javascript"

    ```typescript
    import { markdown } from "@ae_utbm/aemark"

    const result = markdown("this is some *markdown text* with __formatting__");
    ```
