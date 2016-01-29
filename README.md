## Sith AE

### Get started

To start working on the project, just run the following commands:

    git clone https://ae-dev.utbm.fr/ae/Sith.git
    cd Sith
    virtualenv --clear --python=python3 env_sith
    source env_sith/bin/activate
    pip install -r requirements.txt
    ./manage.py setup

To start the simple development server, just run `python3 manage.py runserver`

### Generating documentation

There is a Doxyfile at the root of the project, meaning that if you have Doxygen, you can run `doxygen Doxyfile` to
generate a complete HTML documentation that will be available in the *./doc/html/* folder.

### Dependencies:
  * Django 1.8
  * Pillow

The development is done with sqlite, but it is advised to set a more robust DBMS for production (Postgresql for example)


