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

from ajax_select import LookupChannel, register
from django.core.exceptions import PermissionDenied

from accounting.models import ClubAccount, Company
from club.models import Club
from core.models import Group, SithFile, User
from core.views.site import search_user
from counter.models import Counter, Customer, Product


def check_token(request):
    return (
        "counter_token" in request.session.keys()
        and request.session["counter_token"]
        and Counter.objects.filter(token=request.session["counter_token"]).exists()
    )


class RightManagedLookupChannel(LookupChannel):
    def check_auth(self, request):
        if not request.user.was_subscribed and not check_token(request):
            raise PermissionDenied


@register("users")
class UsersLookup(RightManagedLookupChannel):
    model = User

    def get_query(self, q, request):
        return search_user(q)

    def format_match(self, obj):
        return obj.get_mini_item()

    def format_item_display(self, item):
        return item.get_display_name()


@register("customers")
class CustomerLookup(RightManagedLookupChannel):
    model = Customer

    def get_query(self, q, request):
        users = search_user(q)
        return [user.customer for user in users]

    def format_match(self, obj):
        return obj.user.get_mini_item()

    def format_item_display(self, obj):
        return f"{obj.user.get_display_name()} ({obj.account_id})"


@register("groups")
class GroupsLookup(RightManagedLookupChannel):
    model = Group

    def get_query(self, q, request):
        return self.model.objects.filter(name__icontains=q)[:50]

    def format_match(self, obj):
        return obj.name

    def format_item_display(self, item):
        return item.name


@register("clubs")
class ClubLookup(RightManagedLookupChannel):
    model = Club

    def get_query(self, q, request):
        return self.model.objects.filter(name__icontains=q)[:50]

    def format_match(self, obj):
        return obj.name

    def format_item_display(self, item):
        return item.name


@register("counters")
class CountersLookup(RightManagedLookupChannel):
    model = Counter

    def get_query(self, q, request):
        return self.model.objects.filter(name__icontains=q)[:50]

    def format_item_display(self, item):
        return item.name


@register("products")
class ProductsLookup(RightManagedLookupChannel):
    model = Product

    def get_query(self, q, request):
        return (
            self.model.objects.filter(name__icontains=q)
            | self.model.objects.filter(code__icontains=q)
        ).filter(archived=False)[:50]

    def format_item_display(self, item):
        return "%s (%s)" % (item.name, item.code)


@register("files")
class SithFileLookup(RightManagedLookupChannel):
    model = SithFile

    def get_query(self, q, request):
        return self.model.objects.filter(name__icontains=q)[:50]


@register("club_accounts")
class ClubAccountLookup(RightManagedLookupChannel):
    model = ClubAccount

    def get_query(self, q, request):
        return self.model.objects.filter(name__icontains=q)[:50]

    def format_item_display(self, item):
        return item.name


@register("companies")
class CompaniesLookup(RightManagedLookupChannel):
    model = Company

    def get_query(self, q, request):
        return self.model.objects.filter(name__icontains=q)[:50]

    def format_item_display(self, item):
        return item.name
