.. _direnv:

Utiliser direnv
===============

Pour éviter d'avoir à sourcer l'environnement à chaque fois qu'on rentre dans le projet, il est possible d'utiliser l'utilitaire `direnv <https://direnv.net/>`__.

.. sourcecode:: bash

    # Installation de l'utilitaire

    # Debian et Ubuntu
    sudo apt install direnv
    # Mac
    brew install direnv


    # Installation dans la config
    # Si sur bash
    echo 'eval "$(direnv hook bash)"' >> ~/.bashrc
    # Si sur ZSH
    echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc

    exit # On redémarre le terminal

    # Une fois dans le dossier du projet site AE
    direnv allow .

Une fois que cette configuration a été appliquée, aller dans le dossier du site applique automatiquement l'environnement virtuel, cela fait beaucoup moins de temps perdu pour tout le monde.

Direnv est un utilitaire très puissant et qui peut s'avérer pratique dans bien des situations, n'hésitez pas à aller vous renseigner plus en détail sur celui-ci.