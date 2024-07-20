## Quel terminal utiliser ?

Quel que soit votre configuration, si vous avez réussi à installer
le projet, il y a de fortes chances que bash existe sur
votre ordinateur.
Certains d'entre vous utilisent peut-être un autre shell,
comme `zsh`.

En effet, `bash` est bien, il fait le taff ;
mais son ergonomie finit par montrer ses limites.
C'est pourquoi il existe des shells plus avancés,
qui peuvent améliorer l'ergonomie, la complétion des commandes,
et l'apparence. 
C'est le cas de `zsh`.
Certains vont même plus loin et refont carrément la syntaxe.
C'est le cas de `nu`.

Pour choisir un terminal, demandez-vous juste quel 
est votre usage du terminal :

- Si c'est juste quelques commandes basiques et
que vous ne voulez pas vous embêter à changer
votre configuration, `bash` convient parfaitement.
- Si vous commencez à utilisez le terminal
de manière plus intensive, à varier les commandes
que vous utilisez et/ou que vous voulez customiser
un peu votre expérience, `zsh` est parfait pour vous.
- Si vous aimez la programmation fonctionnelle,
que vous adorez les pipes et que vous voulez faire
des scripts complets mais qui restent lisibles,
`nu` vous plaira à coup sûr.

!!! note

    Ce ne sont que des suggestions.
    Le meilleur choix restera toujours celui
    avec lequel vous êtes le plus confortable.

## Commandes utiles

### Compter le nombre de lignes du projet

=== "bash/zsh"

    ```bash
    sudo apt install cloc
    cloc --exclude-dir=doc,env .
    ```
    Ok, c'est de la triche, on installe un package externe.
    Mais bon, ça marche, et l'équivalent pur bash
    serait carrément plus moche.

=== "nu"

    Nombre de lignes, groupé par fichier :
    ```nu
    ls **/*.py | insert linecount { get name | open | lines | length }
    ```

    Nombre de lignes total :
    ```nu
    ls **/*.py | insert linecount { get name | open | lines | length } | math sum
    ```

    Vous pouvez aussi exlure les lignes vides
    et les les lignes de commentaire :
    ```nu
    ls **/*.py |
    insert linecount {
        get name |
        open |
        lines |
        each { str trim } |
        filter { |l| not ($l | str starts-with "#") } |  # commentaires
        filter { |l| ($l | str length) > 0 } |  # lignes vides
        length
    } |
    math sum
    ```



    

