#
# Copyright 2022
# - Maréchal <thgirod@hotmail.com
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
from functools import cached_property
from urllib.parse import unquote

from django.http import HttpRequest
from django.utils.translation import gettext as _
from pydantic import ValidationError

from eboutic.models import get_eboutic_products
from eboutic.schemas import PurchaseItemList, PurchaseItemSchema


class BasketForm:
    """Class intended to perform checks on the request sended to the server when
    the user submits his basket from /eboutic/.

    Because it must check an unknown number of fields, coming from a cookie
    and needing some databases checks to be performed, inheriting from forms.Form
    or using formset would have been likely to end in a big ball of wibbly-wobbly hacky stuff.
    Thus this class is a pure standalone and performs its operations by its own means.
    However, it still tries to share some similarities with a standard django Form.

    Examples:
        ::

            def my_view(request):
                form = BasketForm(request)
                form.clean()
                if form.is_valid():
                    # perform operations
                else:
                    errors = form.get_error_messages()

                    # return the cookie that was in the request, but with all
                    # incorrects elements removed
                    cookie = form.get_cleaned_cookie()

    You can also use a little shortcut by directly calling `form.is_valid()`
    without calling `form.clean()`. In this case, the latter method shall be
    implicitly called.
    """

    def __init__(self, request: HttpRequest):
        self.user = request.user
        self.cookies = request.COOKIES
        self.error_messages = set()
        self.correct_items = []

    def clean(self) -> None:
        """Perform all the checks, but return nothing.
        To know if the form is valid, the `is_valid()` method must be used.

        The form shall be considered as valid if it meets all the following conditions :
            - it contains a "basket_items" key in the cookies of the request given in the constructor
            - this cookie is a list of objects formatted this way : `[{'id': <int>, 'quantity': <int>,
             'name': <str>, 'unit_price': <float>}, ...]`. The order of the fields in each object does not matter
            - all the ids are positive integers
            - all the ids refer to products available in the EBOUTIC
            - all the ids refer to products the user is allowed to buy
            - all the quantities are positive integers
        """
        try:
            basket = PurchaseItemList.validate_json(
                unquote(self.cookies.get("basket_items", "[]"))
            )
        except ValidationError:
            self.error_messages.add(_("The request was badly formatted."))
            return
        if len(basket) == 0:
            self.error_messages.add(_("Your basket is empty."))
            return
        existing_ids = {product.id for product in get_eboutic_products(self.user)}
        for item in basket:
            # check a product with this id does exist
            if item.product_id in existing_ids:
                self.correct_items.append(item)
            else:
                self.error_messages.add(
                    _(
                        "%(name)s : this product does not exist or may no longer be available."
                    )
                    % {"name": item.name}
                )
                continue
        # this function does not return anything.
        # instead, it fills a set containing the collected error messages
        # an empty set means that no error was seen thus everything is ok
        # and the form is valid.
        # a non-empty set means there was at least one error thus
        # the form is invalid

    def is_valid(self) -> bool:
        """Return True if the form is correct else False.

        If the `clean()` method has not been called beforehand, call it.
        """
        if not self.error_messages and not self.correct_items:
            self.clean()
        if self.error_messages:
            return False
        return True

    @cached_property
    def errors(self) -> list[str]:
        return list(self.error_messages)

    @cached_property
    def cleaned_data(self) -> list[PurchaseItemSchema]:
        return self.correct_items
