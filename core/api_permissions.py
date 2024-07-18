"""Permission classes to be used within ninja-extra controllers.

Some permissions are global (like `IsInGroup` or `IsRoot`),
and some others are per-object (like `CanView` or `CanEdit`).

Examples:
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
"""

from typing import Any

from django.http import HttpRequest
from ninja_extra import ControllerBase
from ninja_extra.permissions import BasePermission


class IsInGroup(BasePermission):
    def __init__(self, group_pk: int):
        self._group_pk = group_pk

    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        return request.user.is_in_group(pk=self._group_pk)


class IsRoot(BasePermission):
    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        return request.user.is_root


class IsSubscriber(BasePermission):
    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        return request.user.is_subscribed


class IsOldSubscriber(BasePermission):
    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        return request.user.was_subscribed


class CanView(BasePermission):
    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        return True

    def has_object_permission(
        self, request: HttpRequest, controller: ControllerBase, obj: Any
    ) -> bool:
        return request.user.can_view(obj)


class CanEdit(BasePermission):
    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        return True

    def has_object_permission(
        self, request: HttpRequest, controller: ControllerBase, obj: Any
    ) -> bool:
        return request.user.can_edit(obj)


class IsOwner(BasePermission):
    def has_permission(self, request: HttpRequest, controller: ControllerBase) -> bool:
        return True

    def has_object_permission(
        self, request: HttpRequest, controller: ControllerBase, obj: Any
    ) -> bool:
        return request.user.is_owner(obj)
