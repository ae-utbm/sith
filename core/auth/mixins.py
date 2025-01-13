#
# Copyright 2016,2017
# - Skia <skia@libskia.so>
# - Sli <antoine@bartuccio.fr>
#
# Ce fichier fait partie du site de l'Association des Étudiants de l'UTBM,
# http://ae.utbm.fr.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License a published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Sofware Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.
#
#

import types
import warnings
from typing import TYPE_CHECKING, Any, LiteralString

from django.contrib.auth.mixins import AccessMixin, PermissionRequiredMixin
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.views.generic.base import View

from core.models import User

if TYPE_CHECKING:
    from django.db.models import Model


def can_edit_prop(obj: Any, user: User) -> bool:
    """Can the user edit the properties of the object.

    Args:
        obj: Object to test for permission
        user: core.models.User to test permissions against

    Returns:
        True if user is authorized to edit object properties else False

    Examples:
        ```python
        if not can_edit_prop(self.object ,request.user):
            raise PermissionDenied
        ```
    """
    return obj is None or user.is_owner(obj)


def can_edit(obj: Any, user: User) -> bool:
    """Can the user edit the object.

    Args:
        obj: Object to test for permission
        user: core.models.User to test permissions against

    Returns:
        True if user is authorized to edit object else False

    Examples:
        ```python
        if not can_edit(self.object, request.user):
            raise PermissionDenied
        ```
    """
    if obj is None or user.can_edit(obj):
        return True
    return can_edit_prop(obj, user)


def can_view(obj: Any, user: User) -> bool:
    """Can the user see the object.

    Args:
        obj: Object to test for permission
        user: core.models.User to test permissions against

    Returns:
        True if user is authorized to see object else False

    Examples:
        ```python
        if not can_view(self.object ,request.user):
            raise PermissionDenied
        ```
    """
    if obj is None or user.can_view(obj):
        return True
    return can_edit(obj, user)


class GenericContentPermissionMixinBuilder(View):
    """Used to build permission mixins.

    This view protect any child view that would be showing an object that is restricted based
      on two properties.

    Attributes:
        raised_error: permission to be raised
    """

    raised_error = PermissionDenied

    @staticmethod
    def permission_function(obj: Any, user: User) -> bool:
        """Function to test permission with."""
        return False

    @classmethod
    def get_permission_function(cls, obj, user):
        return cls.permission_function(obj, user)

    def dispatch(self, request, *arg, **kwargs):
        if hasattr(self, "get_object") and callable(self.get_object):
            self.object = self.get_object()
            if not self.get_permission_function(self.object, request.user):
                raise self.raised_error
            return super().dispatch(request, *arg, **kwargs)

        # If we get here, it's a ListView

        queryset = self.get_queryset()
        l_id = [o.id for o in queryset if self.get_permission_function(o, request.user)]
        if not l_id and queryset.count() != 0:
            raise self.raised_error
        self._get_queryset = self.get_queryset

        def get_qs(self2):
            return self2._get_queryset().filter(id__in=l_id)

        self.get_queryset = types.MethodType(get_qs, self)
        return super().dispatch(request, *arg, **kwargs)


class CanCreateMixin(View):
    """Protect any child view that would create an object.

    Raises:
        PermissionDenied:
            If the user has not the necessary permission
            to create the object of the view.
    """

    def __init_subclass__(cls, **kwargs):
        warnings.warn(
            f"{cls.__name__} is deprecated and should be replaced "
            "by other permission verification mecanism.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init_subclass__(**kwargs)

    def __init__(self, *args, **kwargs):
        warnings.warn(
            f"{self.__class__.__name__} is deprecated and should be replaced "
            "by other permission verification mecanism.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)

    def dispatch(self, request, *arg, **kwargs):
        res = super().dispatch(request, *arg, **kwargs)
        if not request.user.is_authenticated:
            raise PermissionDenied
        return res

    def form_valid(self, form):
        obj = form.instance
        if can_edit_prop(obj, self.request.user):
            return super().form_valid(form)
        raise PermissionDenied


class CanEditPropMixin(GenericContentPermissionMixinBuilder):
    """Ensure the user has owner permissions on the child view object.

    In other word, you can make a view with this view as parent,
    and it will be retricted to the users that are in the
    object's owner_group or that pass the `obj.can_be_viewed_by` test.

    Raises:
        PermissionDenied: If the user cannot see the object
    """

    permission_function = can_edit_prop


class CanEditMixin(GenericContentPermissionMixinBuilder):
    """Ensure the user has permission to edit this view's object.

    Raises:
        PermissionDenied: if the user cannot edit this view's object.
    """

    permission_function = can_edit


class CanViewMixin(GenericContentPermissionMixinBuilder):
    """Ensure the user has permission to view this view's object.

    Raises:
        PermissionDenied: if the user cannot edit this view's object.
    """

    permission_function = can_view


class FormerSubscriberMixin(AccessMixin):
    """Check if the user was at least an old subscriber.

    Raises:
        PermissionDenied: if the user never subscribed.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.was_subscribed:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class PermissionOrAuthorRequiredMixin(PermissionRequiredMixin):
    """Require that the user has the required perm or is the object author.

    This mixin can be used in combination with `DetailView`,
    or another base class that implements the `get_object` method.

    Example:
        In the following code, a user will be able
        to edit news if he has the `com.change_news` permission
        or if he tries to edit his own news :

        ```python
        class NewsEditView(PermissionOrAuthorRequiredMixin, DetailView):
            model = News
            author_field = "author"
            permission_required = "com.change_news"
        ```

        This is more or less equivalent to :

        ```python
        class NewsEditView(PermissionOrAuthorRequiredMixin, DetailView):
            model = News

            def dispatch(self, request, *args, **kwargs):
                self.object = self.get_object()
                if not (
                    user.has_perm("com.change_news")
                    or self.object.author == request.user
                ):
                    raise PermissionDenied
                return super().dispatch(request, *args, **kwargs)
        ```
    """

    author_field: LiteralString = "author"

    def has_permission(self):
        if not hasattr(self, "get_object"):
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} is missing the "
                "get_object attribute. "
                f"Define {self.__class__.__name__}.get_object, "
                "or inherit from a class that implement it (like DetailView)"
            )
        if super().has_permission():
            return True
        if self.request.user.is_anonymous:
            return False
        obj: Model = self.get_object()
        if not self.author_field.endswith("_id"):
            # getting the related model could trigger a db query
            # so we will rather get the foreign value than
            # the object itself.
            self.author_field += "_id"
        author_id = getattr(obj, self.author_field, None)
        return author_id == self.request.user.id
