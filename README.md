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
See requirements.txt

The development is done with sqlite, but it is advised to set a more robust DBMS for production (Postgresql for example)


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




