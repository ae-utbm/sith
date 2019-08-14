.. image:: https://ae-dev.utbm.fr/ae/Sith/badges/master/pipeline.svg
  :target: https://ae-dev.utbm.fr/ae/Sith/commits/master
  :alt: pipeline status

.. image:: https://ae-dev.utbm.fr/ae/Sith/badges/master/coverage.svg
  :target: https://ae-dev.utbm.fr/ae/Sith/commits/master
  :alt: coverage report

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
  :target: https://github.com/ambv/black
  :alt: code style: black

.. image:: https://img.shields.io/badge/zulip-join_chat-brightgreen.svg
  :target: https://ae-dev.zulipchat.com
  :alt: project chat

.. image:: https://readthedocs.org/projects/sith-ae/badge/?version=latest
  :target: https://sith-ae.readthedocs.io/?badge=latest
  :alt: documentation Status

.. body

.. role:: bash(code)
   :language: bash

Sith AE
=======

| **Website** is available here https://ae.utbm.fr/.
| **Documentation** is available here https://sith-ae.readthedocs.io/.

| Please contact us at mailto:ae.info@utbm.fr if you have issues while using our website.
| If you want to join us, you can join our Zulip chat at https://ae-dev.zulipchat.com.

This project is licenced under GNU GPL, see the LICENSE file at the top of the repository for more details.

Controlling the rights
~~~~~~~~~~~~~~~~~~~~~~

When you need to protect an object, there are three levels:

  * Editing the object properties
  * Editing the object various values
  * Viewing the object

Now you have many solutions in your model:

  * You can define a :bash:`is_owned_by(self, user)`, a :bash:`can_be_edited_by(self, user)`, and/or a :bash:`can_be_viewed_by(self, user)` method, each returning True is the user passed can edit/view the object, False otherwise.

    * This allows you to make complex request when the group solution is not powerful enough.
    * It's useful too when you want to define class-wide permissions, e.g. the club members, that are viewable only for Subscribers.

  * You can add an :bash:`owner_group` field, as a ForeignKey to Group.  Second is an :bash:`edit_groups` field, as a ManyToMany to Group, and third is a :bash:`view_groups`, same as for edit.




Finally, when building a class based view, which is highly advised, you just have to inherit it from CanEditPropMixin,
CanEditMixin, or CanViewMixin, which are located in core.views. Your view will then be protected using either the
appropriate group fields, or the right method to check user permissions.
