Commandes utiles
================

* Appliquer le header de licence sur tout le projet

.. code-block:: bash

    for f in $(find . -name "*.py" ! -path "*migration*" ! -path "./env/*" ! -path "./doc/*"); do cat ./doc/header "$f" > /tmp/temp && mv /tmp/temp "$f"; done
