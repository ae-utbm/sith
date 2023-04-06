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

import csv

from django.conf import settings
from django.core.exceptions import NON_FIELD_ERRORS, PermissionDenied, ValidationError
from django.core.paginator import InvalidPage, Paginator
from django.db.models import Sum
from django.http import (
    Http404,
    HttpResponseRedirect,
    StreamingHttpResponse,
)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _t
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView, TemplateView, View
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from club.forms import ClubEditForm, ClubMemberForm, MailingForm, SellingsForm
from club.models import Club, Mailing, MailingSubscription, Membership
from com.views import (
    PosterCreateBaseView,
    PosterDeleteBaseView,
    PosterEditBaseView,
    PosterListBaseView,
)
from core.models import PageRev
from core.views import (
    CanCreateMixin,
    CanEditMixin,
    CanEditPropMixin,
    CanViewMixin,
    DetailFormView,
    PageEditViewBase,
    TabedViewMixin,
    UserIsRootMixin,
)
from counter.models import Selling


class ClubTabsMixin(TabedViewMixin):
    def get_tabs_title(self):
        obj = self.get_object()
        if isinstance(obj, PageRev):
            self.object = obj.page.club
        return self.object.get_display_name()

    def get_list_of_tabs(self):
        tab_list = []
        tab_list.append(
            {
                "url": reverse("club:club_view", kwargs={"club_id": self.object.id}),
                "slug": "infos",
                "name": _("Infos"),
            }
        )
        if self.request.user.can_view(self.object):
            tab_list.append(
                {
                    "url": reverse(
                        "club:club_members", kwargs={"club_id": self.object.id}
                    ),
                    "slug": "members",
                    "name": _("Members"),
                }
            )
            tab_list.append(
                {
                    "url": reverse(
                        "club:club_old_members", kwargs={"club_id": self.object.id}
                    ),
                    "slug": "elderlies",
                    "name": _("Old members"),
                }
            )
        if self.object.page:
            tab_list.append(
                {
                    "url": reverse(
                        "club:club_hist", kwargs={"club_id": self.object.id}
                    ),
                    "slug": "history",
                    "name": _("History"),
                }
            )
        if self.request.user.can_edit(self.object):
            tab_list.append(
                {
                    "url": reverse("club:tools", kwargs={"club_id": self.object.id}),
                    "slug": "tools",
                    "name": _("Tools"),
                }
            )
            tab_list.append(
                {
                    "url": reverse(
                        "club:club_edit", kwargs={"club_id": self.object.id}
                    ),
                    "slug": "edit",
                    "name": _("Edit"),
                }
            )
            if self.object.page and self.request.user.can_edit(self.object.page):
                tab_list.append(
                    {
                        "url": reverse(
                            "core:page_edit",
                            kwargs={"page_name": self.object.page.get_full_name()},
                        ),
                        "slug": "page_edit",
                        "name": _("Edit club page"),
                    }
                )
            tab_list.append(
                {
                    "url": reverse(
                        "club:club_sellings", kwargs={"club_id": self.object.id}
                    ),
                    "slug": "sellings",
                    "name": _("Sellings"),
                }
            )
            tab_list.append(
                {
                    "url": reverse("club:mailing", kwargs={"club_id": self.object.id}),
                    "slug": "mailing",
                    "name": _("Mailing list"),
                }
            )
            tab_list.append(
                {
                    "url": reverse(
                        "club:poster_list", kwargs={"club_id": self.object.id}
                    ),
                    "slug": "posters",
                    "name": _("Posters list"),
                }
            )
        if self.request.user.is_owner(self.object):
            tab_list.append(
                {
                    "url": reverse(
                        "club:club_prop", kwargs={"club_id": self.object.id}
                    ),
                    "slug": "props",
                    "name": _("Props"),
                }
            )
        return tab_list


class ClubListView(ListView):
    """
    List the Clubs
    """

    model = Club
    template_name = "club/club_list.jinja"


class ClubView(ClubTabsMixin, DetailView):
    """
    Front page of a Club
    """

    model = Club
    pk_url_kwarg = "club_id"
    template_name = "club/club_detail.jinja"
    current_tab = "infos"

    def get_context_data(self, **kwargs):
        kwargs = super(ClubView, self).get_context_data(**kwargs)
        if self.object.page and self.object.page.revisions.exists():
            kwargs["page_revision"] = self.object.page.revisions.last().content
        return kwargs


class ClubRevView(ClubView):
    """
    Display a specific page revision
    """

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        self.revision = get_object_or_404(PageRev, pk=kwargs["rev_id"], page__club=obj)
        return super(ClubRevView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super(ClubRevView, self).get_context_data(**kwargs)
        kwargs["page_revision"] = self.revision.content
        return kwargs


class ClubPageEditView(ClubTabsMixin, PageEditViewBase):
    template_name = "club/pagerev_edit.jinja"
    current_tab = "page_edit"

    def dispatch(self, request, *args, **kwargs):
        self.club = get_object_or_404(Club, pk=kwargs["club_id"])
        if not self.club.page:
            raise Http404
        return super(ClubPageEditView, self).dispatch(request, *args, **kwargs)

    def get_object(self):
        self.page = self.club.page
        return self._get_revision()

    def get_success_url(self, **kwargs):
        return reverse_lazy("club:club_view", kwargs={"club_id": self.club.id})


class ClubPageHistView(ClubTabsMixin, CanViewMixin, DetailView):
    """
    Modification hostory of the page
    """

    model = Club
    pk_url_kwarg = "club_id"
    template_name = "club/page_history.jinja"
    current_tab = "history"


class ClubToolsView(ClubTabsMixin, CanEditMixin, DetailView):
    """
    Tools page of a Club
    """

    model = Club
    pk_url_kwarg = "club_id"
    template_name = "club/club_tools.jinja"
    current_tab = "tools"


class ClubMembersView(ClubTabsMixin, CanViewMixin, DetailFormView):
    """
    View of a club's members
    """

    model = Club
    pk_url_kwarg = "club_id"
    form_class = ClubMemberForm
    template_name = "club/club_members.jinja"
    current_tab = "members"

    def get_form_kwargs(self):
        kwargs = super(ClubMembersView, self).get_form_kwargs()
        kwargs["request_user"] = self.request.user
        kwargs["club"] = self.get_object()
        kwargs["club_members"] = self.members
        return kwargs

    def get_context_data(self, *args, **kwargs):
        kwargs = super(ClubMembersView, self).get_context_data(*args, **kwargs)
        kwargs["members"] = self.members
        return kwargs

    def form_valid(self, form):
        """
        Check user rights
        """
        resp = super(ClubMembersView, self).form_valid(form)

        data = form.clean()
        users = data.pop("users", [])
        users_old = data.pop("users_old", [])
        for user in users:
            Membership(club=self.get_object(), user=user, **data).save()
        for user in users_old:
            membership = self.get_object().get_membership_for(user)
            membership.end_date = timezone.now()
            membership.save()
        return resp

    def dispatch(self, request, *args, **kwargs):
        self.members = self.get_object().members.ongoing().order_by("-role")
        return super(ClubMembersView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self, **kwargs):
        return reverse_lazy(
            "club:club_members", kwargs={"club_id": self.get_object().id}
        )


class ClubOldMembersView(ClubTabsMixin, CanViewMixin, DetailView):
    """
    Old members of a club
    """

    model = Club
    pk_url_kwarg = "club_id"
    template_name = "club/club_old_members.jinja"
    current_tab = "elderlies"


class ClubSellingView(ClubTabsMixin, CanEditMixin, DetailFormView):
    """
    Sellings of a club
    """

    model = Club
    pk_url_kwarg = "club_id"
    template_name = "club/club_sellings.jinja"
    current_tab = "sellings"
    form_class = SellingsForm
    paginate_by = 70

    def dispatch(self, request, *args, **kwargs):
        try:
            self.asked_page = int(request.GET.get("page", 1))
        except ValueError:
            raise Http404
        return super(ClubSellingView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(ClubSellingView, self).get_form_kwargs()
        kwargs["club"] = self.object
        return kwargs

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super(ClubSellingView, self).get_context_data(**kwargs)
        qs = Selling.objects.filter(club=self.object)

        kwargs["result"] = qs[:0]
        kwargs["paginated_result"] = kwargs["result"]
        kwargs["total"] = 0
        kwargs["total_quantity"] = 0
        kwargs["benefit"] = 0

        form = self.get_form()
        if form.is_valid():
            if not len([v for v in form.cleaned_data.values() if v is not None]):
                qs = Selling.objects.filter(id=-1)
            if form.cleaned_data["begin_date"]:
                qs = qs.filter(date__gte=form.cleaned_data["begin_date"])
            if form.cleaned_data["end_date"]:
                qs = qs.filter(date__lte=form.cleaned_data["end_date"])

            if form.cleaned_data["counters"]:
                qs = qs.filter(counter__in=form.cleaned_data["counters"])

            selected_products = []
            if form.cleaned_data["products"]:
                selected_products.extend(form.cleaned_data["products"])
            if form.cleaned_data["archived_products"]:
                selected_products.extend(form.cleaned_data["archived_products"])

            if len(selected_products) > 0:
                qs = qs.filter(product__in=selected_products)

            kwargs["result"] = qs.all().order_by("-id")
            kwargs["total"] = sum([s.quantity * s.unit_price for s in kwargs["result"]])
            total_quantity = qs.all().aggregate(Sum("quantity"))
            if total_quantity["quantity__sum"]:
                kwargs["total_quantity"] = total_quantity["quantity__sum"]
            benefit = (
                qs.exclude(product=None).all().aggregate(Sum("product__purchase_price"))
            )
            if benefit["product__purchase_price__sum"]:
                kwargs["benefit"] = benefit["product__purchase_price__sum"]

        kwargs["paginator"] = Paginator(kwargs["result"], self.paginate_by)
        try:
            kwargs["paginated_result"] = kwargs["paginator"].page(self.asked_page)
        except InvalidPage:
            raise Http404

        return kwargs


class ClubSellingCSVView(ClubSellingView):
    """
    Generate sellings in csv for a given period
    """

    class StreamWriter:
        """Implements a file-like interface for streaming the CSV"""

        def write(self, value):
            """Write the value by returning it, instead of storing in a buffer."""
            return value

    def write_selling(self, selling):
        row = [selling.date, selling.counter]
        if selling.seller:
            row.append(selling.seller.get_display_name())
        else:
            row.append("")
        if selling.customer:
            row.append(selling.customer.user.get_display_name())
        else:
            row.append("")
        row = row + [
            selling.label,
            selling.quantity,
            selling.quantity * selling.unit_price,
            selling.get_payment_method_display(),
        ]
        if selling.product:
            row.append(selling.product.selling_price)
            row.append(selling.product.purchase_price)
            row.append(selling.product.selling_price - selling.product.purchase_price)
        else:
            row = row + ["", "", ""]
        return row

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        kwargs = self.get_context_data(**kwargs)

        # Use the StreamWriter class instead of request for streaming
        pseudo_buffer = self.StreamWriter()
        writer = csv.writer(
            pseudo_buffer, delimiter=";", lineterminator="\n", quoting=csv.QUOTE_ALL
        )

        writer.writerow([_t("Quantity"), kwargs["total_quantity"]])
        writer.writerow([_t("Total"), kwargs["total"]])
        writer.writerow([_t("Benefit"), kwargs["benefit"]])
        writer.writerow(
            [
                _t("Date"),
                _t("Counter"),
                _t("Barman"),
                _t("Customer"),
                _t("Label"),
                _t("Quantity"),
                _t("Total"),
                _t("Payment method"),
                _t("Selling price"),
                _t("Purchase price"),
                _t("Benefit"),
            ]
        )

        # Stream response
        response = StreamingHttpResponse(
            (
                writer.writerow(self.write_selling(selling))
                for selling in kwargs["result"]
            ),
            content_type="text/csv",
        )
        name = _("Sellings") + "_" + self.object.name + ".csv"
        response["Content-Disposition"] = "filename=" + name

        return response


class ClubEditView(ClubTabsMixin, CanEditMixin, UpdateView):
    """
    Edit a Club's main informations (for the club's members)
    """

    model = Club
    pk_url_kwarg = "club_id"
    form_class = ClubEditForm
    template_name = "core/edit.jinja"
    current_tab = "edit"


class ClubEditPropView(ClubTabsMixin, CanEditPropMixin, UpdateView):
    """
    Edit the properties of a Club object (for the Sith admins)
    """

    model = Club
    pk_url_kwarg = "club_id"
    fields = ["name", "unix_name", "parent", "is_active"]
    template_name = "core/edit.jinja"
    current_tab = "props"


class ClubCreateView(CanCreateMixin, CreateView):
    """
    Create a club (for the Sith admin)
    """

    model = Club
    pk_url_kwarg = "club_id"
    fields = ["name", "unix_name", "parent"]
    template_name = "core/edit.jinja"


class MembershipSetOldView(CanEditMixin, DetailView):
    """
    Set a membership as beeing old
    """

    model = Membership
    pk_url_kwarg = "membership_id"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.end_date = timezone.now()
        self.object.save()
        return HttpResponseRedirect(
            reverse(
                "club:club_members",
                args=self.args,
                kwargs={"club_id": self.object.club.id},
            )
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return HttpResponseRedirect(
            reverse(
                "club:club_members",
                args=self.args,
                kwargs={"club_id": self.object.club.id},
            )
        )


class MembershipDeleteView(UserIsRootMixin, DeleteView):
    """
    Delete a membership (for admins only)
    """

    model = Membership
    pk_url_kwarg = "membership_id"
    template_name = "core/delete_confirm.jinja"

    def get_success_url(self):
        return reverse_lazy("core:user_clubs", kwargs={"user_id": self.object.user.id})


class ClubStatView(TemplateView):
    template_name = "club/stats.jinja"

    def get_context_data(self, **kwargs):
        kwargs = super(ClubStatView, self).get_context_data(**kwargs)
        kwargs["club_list"] = Club.objects.all()
        return kwargs


class ClubMailingView(ClubTabsMixin, CanEditMixin, DetailFormView):
    """
    A list of mailing for a given club
    """

    model = Club
    form_class = MailingForm
    pk_url_kwarg = "club_id"
    template_name = "club/mailing.jinja"
    current_tab = "mailing"

    def get_form_kwargs(self):
        kwargs = super(ClubMailingView, self).get_form_kwargs()
        kwargs["club_id"] = self.get_object().id
        kwargs["user_id"] = self.request.user.id
        kwargs["mailings"] = self.mailings
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        self.mailings = Mailing.objects.filter(club_id=self.get_object().id).all()
        return super(ClubMailingView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super(ClubMailingView, self).get_context_data(**kwargs)
        kwargs["club"] = self.get_object()
        kwargs["user"] = self.request.user
        kwargs["mailings"] = self.mailings
        kwargs["mailings_moderated"] = (
            kwargs["mailings"].exclude(is_moderated=False).all()
        )
        kwargs["mailings_not_moderated"] = (
            kwargs["mailings"].exclude(is_moderated=True).all()
        )
        kwargs["form_actions"] = {
            "NEW_MALING": self.form_class.ACTION_NEW_MAILING,
            "NEW_SUBSCRIPTION": self.form_class.ACTION_NEW_SUBSCRIPTION,
            "REMOVE_SUBSCRIPTION": self.form_class.ACTION_REMOVE_SUBSCRIPTION,
        }
        return kwargs

    def add_new_mailing(self, cleaned_data) -> ValidationError | None:
        """
        Create a new mailing list from the form
        """
        mailing = Mailing(
            club=self.get_object(),
            email=cleaned_data["mailing_email"],
            moderator=self.request.user,
            is_moderated=False,
        )
        try:
            mailing.clean()
        except ValidationError as validation_error:
            return validation_error
        mailing.save()
        return None

    def add_new_subscription(self, cleaned_data) -> ValidationError | None:
        """
        Add mailing subscriptions for each user given and/or for the specified email in form
        """
        users_to_save = []

        for user in cleaned_data["subscription_users"]:
            sub = MailingSubscription(
                mailing=cleaned_data["subscription_mailing"], user=user
            )
            try:
                sub.clean()
            except ValidationError as validation_error:
                return validation_error

            sub.save()
            users_to_save.append(sub)

        if cleaned_data["subscription_email"]:
            sub = MailingSubscription(
                mailing=cleaned_data["subscription_mailing"],
                email=cleaned_data["subscription_email"],
            )

        try:
            sub.clean()
        except ValidationError as validation_error:
            return validation_error
        sub.save()

        # Save users after we are sure there is no error
        for user in users_to_save:
            user.save()

        return None

    def remove_subscription(self, cleaned_data):
        """
        Remove specified users from a mailing list
        """
        fields = [
            cleaned_data[key]
            for key in cleaned_data.keys()
            if key.startswith("removal_")
        ]
        for field in fields:
            for sub in field:
                sub.delete()

    def form_valid(self, form):
        resp = super(ClubMailingView, self).form_valid(form)

        cleaned_data = form.clean()
        error = None

        if cleaned_data["action"] == self.form_class.ACTION_NEW_MAILING:
            error = self.add_new_mailing(cleaned_data)

        if cleaned_data["action"] == self.form_class.ACTION_NEW_SUBSCRIPTION:
            error = self.add_new_subscription(cleaned_data)

        if cleaned_data["action"] == self.form_class.ACTION_REMOVE_SUBSCRIPTION:
            self.remove_subscription(cleaned_data)

        if error:
            form.add_error(NON_FIELD_ERRORS, error)
            return self.form_invalid(form)

        return resp

    def get_success_url(self, **kwargs):
        return reverse_lazy("club:mailing", kwargs={"club_id": self.get_object().id})


class MailingDeleteView(CanEditMixin, DeleteView):
    model = Mailing
    template_name = "core/delete_confirm.jinja"
    pk_url_kwarg = "mailing_id"
    redirect_page = None

    def dispatch(self, request, *args, **kwargs):
        self.club_id = self.get_object().club.id
        return super(MailingDeleteView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self, **kwargs):
        if self.redirect_page:
            return reverse_lazy(self.redirect_page)
        else:
            return reverse_lazy("club:mailing", kwargs={"club_id": self.club_id})


class MailingSubscriptionDeleteView(CanEditMixin, DeleteView):
    model = MailingSubscription
    template_name = "core/delete_confirm.jinja"
    pk_url_kwarg = "mailing_subscription_id"

    def dispatch(self, request, *args, **kwargs):
        self.club_id = self.get_object().mailing.club.id
        return super(MailingSubscriptionDeleteView, self).dispatch(
            request, *args, **kwargs
        )

    def get_success_url(self, **kwargs):
        return reverse_lazy("club:mailing", kwargs={"club_id": self.club_id})


class MailingAutoGenerationView(View):
    def dispatch(self, request, *args, **kwargs):
        self.mailing = get_object_or_404(Mailing, pk=kwargs["mailing_id"])
        if not request.user.can_edit(self.mailing):
            raise PermissionDenied
        return super(MailingAutoGenerationView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        club = self.mailing.club
        self.mailing.subscriptions.all().delete()
        members = club.members.filter(
            role__gte=settings.SITH_CLUB_ROLES_ID["Board member"]
        ).exclude(end_date__lte=timezone.now())
        for member in members.all():
            MailingSubscription(user=member.user, mailing=self.mailing).save()
        return redirect("club:mailing", club_id=club.id)


class PosterListView(ClubTabsMixin, PosterListBaseView, CanViewMixin):
    """List communication posters"""

    def get_object(self):
        return self.club

    def get_context_data(self, **kwargs):
        kwargs = super(PosterListView, self).get_context_data(**kwargs)
        kwargs["app"] = "club"
        kwargs["club"] = self.club
        return kwargs


class PosterCreateView(PosterCreateBaseView, CanCreateMixin):
    """Create communication poster"""

    pk_url_kwarg = "club_id"

    def get_object(self):
        obj = super(PosterCreateView, self).get_object()
        if not obj:
            return self.club
        return obj

    def get_success_url(self, **kwargs):
        return reverse_lazy("club:poster_list", kwargs={"club_id": self.club.id})


class PosterEditView(ClubTabsMixin, PosterEditBaseView, CanEditMixin):
    """Edit communication poster"""

    def get_success_url(self):
        return reverse_lazy("club:poster_list", kwargs={"club_id": self.club.id})

    def get_context_data(self, **kwargs):
        kwargs = super(PosterEditView, self).get_context_data(**kwargs)
        kwargs["app"] = "club"
        return kwargs


class PosterDeleteView(PosterDeleteBaseView, ClubTabsMixin, CanEditMixin):
    """Delete communication poster"""

    def get_success_url(self):
        return reverse_lazy("club:poster_list", kwargs={"club_id": self.club.id})
