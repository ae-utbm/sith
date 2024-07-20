Pour éviter d'avoir à sourcer l'environnement 
à chaque fois qu'on rentre dans le projet,
il est possible d'utiliser l'utilitaire [direnv](https://direnv.net/).

Comme pour beaucoup de choses, il faut commencer par l'installer :

=== "Linux"

    === "Debian/Ubuntu"

        ```bash
        sudo apt install direnv
        ```

    === "Arch Linux"

        ```bash
        sudo pacman -S direnv
        ```

=== "macOS"

    ```bash
    brew install direnv
    ```

Puis on configure :

=== "bash"

    ```bash
    echo 'eval "$(direnv hook bash)"' >> ~/.bashrc
    exit # On redémarre le terminal
    ```

=== "zsh"

    ```zsh
    echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc
    exit # On redémarre le terminal
    ```

=== "nu"

    Désolé, par `direnv hook` pour `nu`

Une fois le terminal redémarré, dans le répertoire du projet :
```bash
direnv allow .
```

Une fois que cette configuration a été appliquée, 
aller dans le dossier du site applique automatiquement 
l'environnement virtuel.
Ça peut faire gagner pas mal de temps.

Direnv est un utilitaire très puissant 
et qui peut s'avérer pratique dans bien des situations,
n'hésitez pas à aller vous renseigner plus en détail sur celui-ci.