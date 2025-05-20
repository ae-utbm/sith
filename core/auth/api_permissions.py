"""Permission classes to be used within ninja-extra controllers.

Some permissions are global (like `IsInGroup` or `IsRoot`),
and some others are per-object (like `CanView` or `CanEdit`).

Example:
    ```python
    # restrict all the routes of this controller
    # to subscribed users
    @api_controller("/foo", permissions=[IsSubscriber])
    class FooController(ControllerBase):
        @route.get("/bar")
        def bar_get(self):
            # This route inherits the permissions of the controller
            # ...

        @route.bar("/bar/{bar_id}", permissions=[CanView])
        def bar_get_one(self, bar_id: int):
            # per-object permission resolution happens
            # when calling either the `get_object_or_exception`
            # or `get_object_or_none` method.
            bar = self.get_object_or_exception(Counter, pk=bar_id)

            # you can also call the `check_object_permission` manually
            other_bar = Counter.objects.first()
            self.check_object_permissions(other_bar)

            # ...

        # This route is restricted to counter admins and root users
        @route.delete(
            "/bar/{bar_id}",
            permissions=[IsRoot | IsInGroup(settings.SITH_GROUP_COUNTER_ADMIN_ID)
        ]
        def bar_delete(self, bar_id: int):
            # ...
    ```
"""

import operator
from functools import reduce
from typing import Any

from django.contrib.auth.models import Permission
from django.http import HttpRequest
from ninja_extra import ControllerBase
from ninja_extra.permissions import BasePermission

from counter.models import Counter


class IsInGroup(BasePermission):
    """Check that the user is in the group whose primary key is given."""

    def __init__(self, group_pk: int):
        self._group_pk = group_pk

    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        return request.user.is_in_group(pk=self._group_pk)


class HasPerm(BasePermission):
    """Check that the user has the required perm.

    If multiple perms are given, a comparer function can also be passed,
    in order to change the way perms are checked.

    Example:
        ```python
        # this route will require both permissions
        @route.put("/foo", permissions=[HasPerm(["foo.change_foo", "foo.add_foo"])]
        def foo(self): ...

        # This route will require at least one of the perm,
        # but it's not mandatory to have all of them
        @route.put(
            "/bar",
            permissions=[HasPerm(["foo.change_bar", "foo.add_bar"], op=operator.or_)],
        )
        def bar(self): ...
    """

    def __init__(
        self, perms: str | Permission | list[str | Permission], op=operator.and_
    ):
        """
        Args:
            perms: a permission or a list of permissions the user must have
            op: An operator to combine multiple permissions (in most cases,
                it will be either `operator.and_` or `operator.or_`)
        """
        super().__init__()
        if not isinstance(perms, (list, tuple, set)):
            perms = [perms]
        self._operator = op
        self._perms = perms

    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        # if the request has the `auth` property,
        # it means that the user has been explicitly authenticated
        # using a django-ninja authentication backend
        # (whether it is SessionAuth or ApiKeyAuth).
        # If not, this authentication has not been done, but the user may
        # still be implicitly authenticated through AuthenticationMiddleware
        user = request.auth if hasattr(request, "auth") else request.user
        # `user` may either be a `core.User` or an `apikey.ApiClient` ;
        # they are not the same model, but they both implement the `has_perm` method
        return reduce(self._operator, (user.has_perm(p) for p in self._perms))


class IsRoot(BasePermission):
    """Check that the user is root."""

    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        return request.user.is_root


class IsSubscriber(BasePermission):
    """Check that the user is currently subscribed."""

    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        return request.user.is_subscribed


class IsOldSubscriber(BasePermission):
    """Check that the user has at least one subscription in its history."""

    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        return request.user.was_subscribed


class CanView(BasePermission):
    """Check that this user has the permission to view the object of this route.

    Wrap the `user.can_view(obj)` method.
    To see an example, look at the example in the module docstring.
    """

    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        return True

    def has_object_permission(
        self, request: HttpRequest, controller: ControllerBase, obj: Any
    ) -> bool:
        return request.user.can_view(obj)


class CanEdit(BasePermission):
    """Check that this user has the permission to edit the object of this route.

    Wrap the `user.can_edit(obj)` method.
    To see an example, look at the example in the module docstring.
    """

    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        return True

    def has_object_permission(
        self, request: HttpRequest, controller: ControllerBase, obj: Any
    ) -> bool:
        return request.user.can_edit(obj)


class IsOwner(BasePermission):
    """Check that this user owns the object of this route.

    Wrap the `user.is_owner(obj)` method.
    To see an example, look at the example in the module docstring.
    """

    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        return True

    def has_object_permission(
        self, request: HttpRequest, controller: ControllerBase, obj: Any
    ) -> bool:
        return request.user.is_owner(obj)


class IsLoggedInCounter(BasePermission):
    """Check that a user is logged in a counter."""

    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        if "/counter/" not in request.META.get("HTTP_REFERER", ""):
            return False
        token = request.session.get("counter_token")
        if not token:
            return False
        return Counter.objects.filter(token=token).exists()


CanAccessLookup = IsOldSubscriber | IsRoot | IsLoggedInCounter
