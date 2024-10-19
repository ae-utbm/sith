#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the source code of the website at https://github.com/ae-utbm/sith
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
#

from ajax_select import LookupChannel, register
from django.core.exceptions import PermissionDenied

from accounting.models import ClubAccount, Company
from club.models import Club
from core.models import Group, SithFile, User
from core.views.site import search_user
from counter.models import Counter, Customer, Product
from counter.utils import is_logged_in_counter


class RightManagedLookupChannel(LookupChannel):
    def check_auth(self, request):
        if not request.user.was_subscribed and not is_logged_in_counter(request):
            raise PermissionDenied


@register("users")  # Migrated
class UsersLookup(RightManagedLookupChannel):
    model = User

    def get_query(self, q, request):
        return search_user(q)

    def format_match(self, obj):
        return obj.get_mini_item()

    def format_item_display(self, item):
        return item.get_display_name()


@register("customers")  # Never used
class CustomerLookup(RightManagedLookupChannel):
    model = Customer

    def get_query(self, q, request):
        return list(Customer.objects.filter(user__in=search_user(q)))

    def format_match(self, obj):
        return obj.user.get_mini_item()

    def format_item_display(self, obj):
        return f"{obj.user.get_display_name()} ({obj.account_id})"


@register("groups")  # Migrated
class GroupsLookup(RightManagedLookupChannel):
    model = Group

    def get_query(self, q, request):
        return self.model.objects.filter(name__icontains=q)[:50]

    def format_match(self, obj):
        return obj.name

    def format_item_display(self, item):
        return item.name


@register("clubs")  # Migrated
class ClubLookup(RightManagedLookupChannel):
    model = Club

    def get_query(self, q, request):
        return self.model.objects.filter(name__icontains=q)[:50]

    def format_match(self, obj):
        return obj.name

    def format_item_display(self, item):
        return item.name


@register("counters")  # Migrated
class CountersLookup(RightManagedLookupChannel):
    model = Counter

    def get_query(self, q, request):
        return self.model.objects.filter(name__icontains=q)[:50]

    def format_item_display(self, item):
        return item.name


@register("products")  # Migrated
class ProductsLookup(RightManagedLookupChannel):
    model = Product

    def get_query(self, q, request):
        return (
            self.model.objects.filter(name__icontains=q)
            | self.model.objects.filter(code__icontains=q)
        ).filter(archived=False)[:50]

    def format_item_display(self, item):
        return "%s (%s)" % (item.name, item.code)


@register("files")  # Migrated
class SithFileLookup(RightManagedLookupChannel):
    model = SithFile

    def get_query(self, q, request):
        return self.model.objects.filter(name__icontains=q)[:50]


@register("club_accounts")  # Migrated
class ClubAccountLookup(RightManagedLookupChannel):
    model = ClubAccount

    def get_query(self, q, request):
        return self.model.objects.filter(name__icontains=q)[:50]

    def format_item_display(self, item):
        return item.name


@register("companies")  # Migrated
class CompaniesLookup(RightManagedLookupChannel):
    model = Company

    def get_query(self, q, request):
        return self.model.objects.filter(name__icontains=q)[:50]

    def format_item_display(self, item):
        return item.name
