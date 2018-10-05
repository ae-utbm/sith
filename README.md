[![pipeline status](https://ae-dev.utbm.fr/ae/Sith/badges/master/pipeline.svg)](https://ae-dev.utbm.fr/ae/Sith/commits/master)
[![coverage report](https://ae-dev.utbm.fr/ae/Sith/badges/master/coverage.svg)](https://ae-dev.utbm.fr/ae/Sith/commits/master)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

## Sith AE

### Get started

To start working on the project, just run the following commands:

    git clone https://ae-dev.utbm.fr/ae/Sith.git
    cd Sith
    virtualenv --clear --python=python3 env
    source env/bin/activate
    pip install -r requirements.txt
    ./manage.py setup

To start the simple development server, just run `python3 manage.py runserver`

### Generating documentation

There is a Doxyfile at the root of the project, meaning that if you have Doxygen, you can run `doxygen Doxyfile` to
generate a complete HTML documentation that will be available in the *./doc/html/* folder.

### Dependencies:
See requirements.txt

You may need to install some dev libraries like `libmysqlclient-dev`, `libssl-dev`, `libjpeg-dev`, or `zlib1g-dev` to install all the
requiered dependancies with pip. You may also need `mysql-client`. Don't also forget `python3-dev` if you don't have it
already.

You can check all of them with:

```
sudo apt install libmysqlclient-dev libssl-dev libjpeg-dev zlib1g-dev python3-dev libffi-dev python3-dev libgraphviz-dev pkg-config
```

The development is done with sqlite, but it is advised to set a more robust DBMS for production (Postgresql for example)

### Collecting statics for production:

We use scss in the project. In development environment (DEBUG=True), scss is compiled every time the file is needed. For production, it assumes you have already compiled every files and to do so, you need to use the following commands : 

```
./manage.py collectstatic # To collect statics
./manage.py compilestatic # To compile scss in those statics
```

### Misc about development

#### Controlling the rights

When you need to protect an object, there are three levels:
  * Editing the object properties
  * Editing the object various values
  * Viewing the object

Now you have many solutions in your model:
  * You can define a `is_owned_by(self, user)`, a `can_be_edited_by(self, user)`, and/or a `can_be_viewed_by(self, user)`
    method, each returning True is the user passed can edit/view the object, False otherwise.   
    This allows you to make complex request when the group solution is not powerful enough.    
    It's useful too when you want to define class-wide permissions, e.g. the club members, that are viewable only for
    Subscribers.
  * You can add an `owner_group` field, as a ForeignKey to Group.  Second is an `edit_groups` field, as a ManyToMany to
    Group, and third is a `view_groups`, same as for edit.

Finally, when building a class based view, which is highly advised, you just have to inherit it from CanEditPropMixin,
CanEditMixin, or CanViewMixin, which are located in core.views. Your view will then be protected using either the
appropriate group fields, or the right method to check user permissions.

#### Counting the number of line of code

```
# apt install cloc
$ cloc --exclude-dir=doc,env .
```

#### Updating doc/SYNTAX.md

If you make an update in the Markdown syntax parser, it's good to document
update the syntax reference page in `doc/SYNTAX.md`. But updating this file will
break the tests if you don't update the corresponding `doc/SYNTAX.html` file at
the same time.  
To do that, simply run `./manage.py markdown > doc/SYNTAX.html`,
and the tests should pass again.


