# -*- coding:utf-8 -*-
#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
# All contributors are listed in the CONTRIBUTORS file.
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the whole source code at https://github.com/ae-utbm/sith3
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
# PREVIOUSLY LICENSED UNDER THE MIT LICENSE,
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE.old
# OR WITHIN THE LOCAL FILE "LICENSE.old"
#
#
#

import json
import re
import typing
from urllib.parse import unquote

from django.http import HttpRequest
from django.utils.translation import gettext as _
from sentry_sdk import capture_message

from eboutic.models import get_eboutic_products


class BasketForm:
    """
    Class intended to perform checks on the request sended to the server when
    the user submits his basket from /eboutic/

    Because it must check an unknown number of fields, coming from a cookie
    and needing some databases checks to be performed, inheriting from forms.Form
    or using formset would have been likely to end in a big ball of wibbly-wobbly hacky stuff.
    Thus this class is a pure standalone and performs its operations by its own means.
    However, it still tries to share some similarities with a standard django Form.

    Example:
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

    # check the json is an array containing non-nested objects.
    # values must be strings or numbers
    # this is matched :
    # [{"id": 4, "name": "[PROMO 22] badges", "unit_price": 2.3, "quantity": 2}]
    # but this is not :
    # [{"id": {"nested_id": 10}, "name": "[PROMO 22] badges", "unit_price": 2.3, "quantity": 2}]
    # and neither does this :
    # [{"id": ["nested_id": 10], "name": "[PROMO 22] badges", "unit_price": 2.3, "quantity": 2}]
    # and neither does that :
    # [{"id": null, "name": "[PROMO 22] badges", "unit_price": 2.3, "quantity": 2}]
    json_cookie_re = re.compile(
        r"^\[\s*(\{\s*(\"[^\"]*\":\s*(\"[^\"]{0,64}\"|\d{0,5}\.?\d+),?\s*)*\},?\s*)*\s*\]$"
    )

    def __init__(self, request: HttpRequest):
        self.user = request.user
        self.cookies = request.COOKIES
        self.error_messages = set()
        self.correct_cookie = []

    def clean(self) -> None:
        """
        Perform all the checks, but return nothing.
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
        # replace escaped double quotes by single quotes, as the RegEx used to check the json
        # does not support escaped double quotes
        basket = unquote(self.cookies.get("basket_items", "")).replace('\\"', "'")

        if basket in ("[]", ""):
            self.error_messages.add(_("You have no basket."))
            return

        # check that the json is not nested before parsing it to make sure
        # malicious user can't DDoS the server with deeply nested json
        if not BasketForm.json_cookie_re.match(basket):
            # As the validation of the cookie goes through a rather boring regex,
            # we can regularly have to deal with subtle errors that we hadn't forecasted,
            # so we explicitly lay a Sentry message capture here.
            capture_message(
                "Eboutic basket regex checking failed to validate basket json",
                level="error",
            )
            self.error_messages.add(_("The request was badly formatted."))
            return

        try:
            basket = json.loads(basket)
        except json.JSONDecodeError:
            self.error_messages.add(_("The basket cookie was badly formatted."))
            return

        if type(basket) is not list or len(basket) == 0:
            self.error_messages.add(_("Your basket is empty."))
            return

        for item in basket:
            expected_keys = {"id", "quantity", "name", "unit_price"}
            if type(item) is not dict or set(item.keys()) != expected_keys:
                self.error_messages.add("One or more items are badly formatted.")
                continue
            # check the id field is a positive integer
            if type(item["id"]) is not int or item["id"] < 0:
                self.error_messages.add(
                    _("%(name)s : this product does not exist.")
                    % {"name": item["name"]}
                )
                continue
            # check a product with this id does exist
            ids = {product.id for product in get_eboutic_products(self.user)}
            if not item["id"] in ids:
                self.error_messages.add(
                    _(
                        "%(name)s : this product does not exist or may no longer be available."
                    )
                    % {"name": item["name"]}
                )
                continue
            if type(item["quantity"]) is not int or item["quantity"] < 0:
                self.error_messages.add(
                    _("You cannot buy %(nbr)d %(name)s.")
                    % {"nbr": item["quantity"], "name": item["name"]}
                )
                continue

            # if we arrive here, it means this item has passed all tests
            self.correct_cookie.append(item)
        # for loop for item checking ends here

        # this function does not return anything.
        # instead, it fills a set containing the collected error messages
        # an empty set means that no error was seen thus everything is ok
        # and the form is valid.
        # a non-empty set means there was at least one error thus
        # the form is invalid

    def is_valid(self) -> bool:
        """
        return True if the form is correct else False.
        If the `clean()` method has not been called beforehand, call it
        """
        if self.error_messages == set() and self.correct_cookie == []:
            self.clean()
        if self.error_messages:
            return False
        return True

    def get_error_messages(self) -> typing.List[str]:
        return list(self.error_messages)

    def get_cleaned_cookie(self) -> str:
        if not self.correct_cookie:
            return ""
        return json.dumps(self.correct_cookie)
