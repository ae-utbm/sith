.. image:: https://ae-dev.utbm.fr/ae/Sith/badges/master/pipeline.svg
  :target: https://ae-dev.utbm.fr/ae/Sith/commits/master
  :alt: pipeline status

.. image:: https://ae-dev.utbm.fr/ae/Sith/badges/master/coverage.svg
  :target: https://ae-dev.utbm.fr/ae/Sith/commits/master
  :alt: coverage report

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
  :target: https://github.com/ambv/black
  :alt: Code style: black

.. image:: https://img.shields.io/badge/zulip-join_chat-brightgreen.svg
  :target: https://ae-dev.zulipchat.com
  :alt: project chat

.. image:: https://readthedocs.org/projects/sith-ae/badge/?version=latest
  :target: https://sith-ae.readthedocs.io/?badge=latest
  :alt: Documentation Status

.. body

Sith AE
=======

Logging errors with sentry
--------------------------

To connect the app to sentry.io, you must set the variable SENTRY_DSN in your settings custom. It's composed of the full link given on your sentry project

Collecting statics for production:
----------------------------------

We use scss in the project. In development environment (DEBUG=True), scss is compiled every time the file is needed. For production, it assumes you have already compiled every files and to do so, you need to use the following commands : 

.. sourcecode:: bash

  ./manage.py collectstatic # To collect statics
  ./manage.py compilestatic # To compile scss in those statics

Misc about development
----------------------

Controlling the rights
~~~~~~~~~~~~~~~~~~~~~~


When you need to protect an object, there are three levels:

  * Editing the object properties
  * Editing the object various values
  * Viewing the object

Now you have many solutions in your model:

  * You can define a `is_owned_by(self, user)`, a `can_be_edited_by(self, user)`, and/or a `can_be_viewed_by(self, user)` method, each returning True is the user passed can edit/view the object, False otherwise.

    * This allows you to make complex request when the group solution is not powerful enough.
    * It's useful too when you want to define class-wide permissions, e.g. the club members, that are viewable only for Subscribers.

  * You can add an `owner_group` field, as a ForeignKey to Group.  Second is an `edit_groups` field, as a ManyToMany to Group, and third is a `view_groups`, same as for edit.

Finally, when building a class based view, which is highly advised, you just have to inherit it from CanEditPropMixin,
CanEditMixin, or CanViewMixin, which are located in core.views. Your view will then be protected using either the
appropriate group fields, or the right method to check user permissions.

Counting the number of line of code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. sourcecode:: bash

  sudo apt install cloc
  cloc --exclude-dir=doc,env .

Updating doc/SYNTAX.md
~~~~~~~~~~~~~~~~~~~~~~

| If you make an update in the Markdown syntax parser, it's good to document update the syntax reference page in `doc/SYNTAX.md`. But updating this file will break the tests if you don't update the corresponding `doc/SYNTAX.html` file at the same time.
| To do that, simply run `./manage.py markdown > doc/SYNTAX.html`,
and the tests should pass again.


