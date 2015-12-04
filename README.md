## Sith AE


To start working on the project, just run the following commands:

    git clone https://ae-dev.utbm.fr/ae/Sith.git
    cd Sith
    virtualenv --clear --python=python3 env_sith
    source env_sith/bin/activate
    pip install -r requirements.txt
    ./manage.py setup

To load some initial data in the core:

    python3 manage.py loaddata users groups pages

You will be prompted for your Gitlab account, so you need some.

To start the debug server, just run `python3 manage.py runserver`

#### Dependencies:
  * Django 1.8

The development is done with sqlite, but it is advised to set a more robust
DBMS for production (Postgresql for example)
