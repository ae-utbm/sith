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

import csv
from typing import Any

from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import NON_FIELD_ERRORS, PermissionDenied, ValidationError
from django.core.paginator import InvalidPage, Paginator
from django.db.models import Q, Sum
from django.http import (
    Http404,
    HttpResponseRedirect,
    StreamingHttpResponse,
)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.safestring import SafeString
from django.utils.timezone import now
from django.utils.translation import gettext as _t
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView, View
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from club.forms import (
    ClubAdminEditForm,
    ClubEditForm,
    ClubMemberForm,
    ClubOldMemberForm,
    MailingForm,
    SellingsForm,
)
from club.models import (
    Club,
    Mailing,
    MailingSubscription,
    Membership,
)
from com.models import Poster
from com.views import (
    PosterCreateBaseView,
    PosterDeleteBaseView,
    PosterEditBaseView,
    PosterListBaseView,
)
from core.auth.mixins import (
    CanEditMixin,
)
from core.models import PageRev
from core.views import DetailFormView, PageEditViewBase, UseFragmentsMixin
from core.views.mixins import FragmentMixin, FragmentRenderer, TabedViewMixin
from counter.models import Selling


class ClubTabsMixin(TabedViewMixin):
    def get_tabs_title(self):
        if not hasattr(self, "object") or not self.object:
            self.object = self.get_object()
        if isinstance(self.object, PageRev):
            self.object = self.object.page.club
        elif isinstance(self.object, Poster):
            self.object = self.object.club
        return self.object.get_display_name()

    def get_list_of_tabs(self):
        tab_list = [
            {
                "url": reverse("club:club_view", kwargs={"club_id": self.object.id}),
                "slug": "infos",
                "name": _("Infos"),
            }
        ]
        if self.request.user.has_perm("club.view_club"):
            tab_list.extend(
                [
                    {
                        "url": reverse(
                            "club:club_members", kwargs={"club_id": self.object.id}
                        ),
                        "slug": "members",
                        "name": _("Members"),
                    },
                    {
                        "url": reverse(
                            "club:club_old_members", kwargs={"club_id": self.object.id}
                        ),
                        "slug": "elderlies",
                        "name": _("Old members"),
                    },
                ]
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
            tab_list.extend(
                [
                    {
                        "url": reverse(
                            "club:tools", kwargs={"club_id": self.object.id}
                        ),
                        "slug": "tools",
                        "name": _("Tools"),
                    },
                    {
                        "url": reverse(
                            "club:club_edit", kwargs={"club_id": self.object.id}
                        ),
                        "slug": "edit",
                        "name": _("Edit"),
                    },
                ]
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
            tab_list.extend(
                [
                    {
                        "url": reverse(
                            "club:club_sellings", kwargs={"club_id": self.object.id}
                        ),
                        "slug": "sellings",
                        "name": _("Sellings"),
                    },
                    {
                        "url": reverse(
                            "club:mailing", kwargs={"club_id": self.object.id}
                        ),
                        "slug": "mailing",
                        "name": _("Mailing list"),
                    },
                    {
                        "url": reverse(
                            "club:poster_list", kwargs={"club_id": self.object.id}
                        ),
                        "slug": "posters",
                        "name": _("Posters"),
                    },
                ]
            )
        return tab_list


class ClubListView(ListView):
    """List the Clubs."""

    model = Club
    template_name = "club/club_list.jinja"
    queryset = (
        Club.objects.filter(parent=None).order_by("name").prefetch_related("children")
    )
    context_object_name = "club_list"


class ClubView(ClubTabsMixin, DetailView):
    """Front page of a Club."""

    model = Club
    pk_url_kwarg = "club_id"
    template_name = "club/club_detail.jinja"
    current_tab = "infos"

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["page_revision"] = (
            PageRev.objects.filter(page_id=self.object.page_id)
            .order_by("-date")
            .values_list("content", flat=True)
            .first()
        )
        return kwargs


class ClubRevView(ClubView):
    """Display a specific page revision."""

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        self.revision = get_object_or_404(PageRev, pk=kwargs["rev_id"], page__club=obj)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["page_revision"] = self.revision.content
        return kwargs


class ClubPageEditView(ClubTabsMixin, PageEditViewBase):
    template_name = "club/pagerev_edit.jinja"
    current_tab = "page_edit"

    def dispatch(self, request, *args, **kwargs):
        self.club = get_object_or_404(Club, pk=kwargs["club_id"])
        if not self.club.page:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        self.page = self.club.page
        return self._get_revision()

    def get_success_url(self, **kwargs):
        return reverse_lazy("club:club_view", kwargs={"club_id": self.club.id})


class ClubPageHistView(ClubTabsMixin, PermissionRequiredMixin, DetailView):
    """Modification hostory of the page."""

    model = Club
    pk_url_kwarg = "club_id"
    template_name = "club/page_history.jinja"
    current_tab = "history"
    permission_required = "club.view_club"


class ClubToolsView(ClubTabsMixin, CanEditMixin, DetailView):
    """Tools page of a Club."""

    model = Club
    pk_url_kwarg = "club_id"
    template_name = "club/club_tools.jinja"
    current_tab = "tools"


class ClubAddMembersFragment(
    FragmentMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView
):
    template_name = "club/fragments/add_member.jinja"
    form_class = ClubMemberForm
    model = Membership
    object = None
    reload_on_redirect = True
    permission_required = "club.view_club"
    success_message = _("%(user)s has been added to club.")

    def dispatch(self, *args, **kwargs):
        club_id = self.kwargs.get("club_id")
        if not club_id:
            raise Http404
        self.club = get_object_or_404(Club, pk=kwargs.get("club_id"))
        return super().dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {
            "request_user": self.request.user,
            "club": self.club,
        }

    def render_fragment(self, request, **kwargs) -> SafeString:
        self.club = kwargs.get("club")
        return super().render_fragment(request, **kwargs)

    def get_success_url(self):
        return reverse("club:club_members", kwargs={"club_id": self.club.id})

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {"club": self.club}


class ClubMembersView(
    ClubTabsMixin, UseFragmentsMixin, PermissionRequiredMixin, DetailFormView
):
    """View of a club's members."""

    model = Club
    pk_url_kwarg = "club_id"
    form_class = ClubOldMemberForm
    template_name = "club/club_members.jinja"
    current_tab = "members"
    permission_required = "club.view_club"

    def get_fragments(self) -> dict[str, type[FragmentMixin] | FragmentRenderer]:
        membership = self.object.get_membership_for(self.request.user)
        if (
            membership
            and membership.role <= settings.SITH_MAXIMUM_FREE_ROLE
            and not self.request.user.has_perm("club.add_membership")
        ):
            return {}
        return {"add_member_fragment": ClubAddMembersFragment}

    def get_fragment_data(self) -> dict[str, Any]:
        return {"add_member_fragment": {"club": self.object}}

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {
            "user": self.request.user,
            "club": self.object,
        }

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        editable = list(
            kwargs["form"].fields["members_old"].queryset.values_list("id", flat=True)
        )
        kwargs["members"] = list(
            self.object.members.ongoing()
            .annotate(is_editable=Q(id__in=editable))
            .order_by("-role")
            .select_related("user")
        )
        kwargs["can_end_membership"] = len(editable) > 0
        return kwargs

    def form_valid(self, form):
        for membership in form.cleaned_data.get("members_old"):
            membership.end_date = now()
            membership.save()
        return super().form_valid(form)

    def get_success_url(self, **kwargs):
        return self.request.path


class ClubOldMembersView(ClubTabsMixin, PermissionRequiredMixin, DetailView):
    """Old members of a club."""

    model = Club
    pk_url_kwarg = "club_id"
    template_name = "club/club_old_members.jinja"
    current_tab = "elderlies"
    permission_required = "club.view_club"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "old_members": (
                self.object.members.exclude(end_date=None)
                .order_by("-role", "description", "-end_date")
                .select_related("user")
            )
        }


class ClubSellingView(ClubTabsMixin, CanEditMixin, DetailFormView):
    """Sellings of a club."""

    model = Club
    pk_url_kwarg = "club_id"
    template_name = "club/club_sellings.jinja"
    current_tab = "sellings"
    form_class = SellingsForm
    paginate_by = 70

    def dispatch(self, request, *args, **kwargs):
        try:
            self.asked_page = int(request.GET.get("page", 1))
        except ValueError as e:
            raise Http404 from e
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["club"] = self.object
        return kwargs

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        qs = Selling.objects.filter(club=self.object)

        kwargs["result"] = qs[:0]
        kwargs["paginated_result"] = kwargs["result"]
        kwargs["total"] = 0
        kwargs["total_quantity"] = 0
        kwargs["benefit"] = 0

        form = self.get_form()
        if form.is_valid():
            if not len([v for v in form.cleaned_data.values() if v is not None]):
                qs = Selling.objects.none()
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

            kwargs["result"] = qs.select_related(
                "counter", "counter__club", "customer", "customer__user", "seller"
            ).order_by("-id")
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
        except InvalidPage as e:
            raise Http404 from e

        return kwargs


class ClubSellingCSVView(ClubSellingView):
    """Generate sellings in csv for a given period."""

    class StreamWriter:
        """Implements a file-like interface for streaming the CSV."""

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
        row = [
            *row,
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
            row = [*row, "", "", ""]
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
    """Edit a Club.

    Regular club board members will be able to edit the main infos
    (like the logo and the description).
    Admins will also be able to edit the club properties
    (like the name and the parent club).
    """

    model = Club
    pk_url_kwarg = "club_id"
    template_name = "club/edit_club.jinja"
    current_tab = "edit"

    def get_form_class(self):
        if self.object.is_owned_by(self.request.user):
            return ClubAdminEditForm
        return ClubEditForm


class ClubCreateView(PermissionRequiredMixin, CreateView):
    """Create a club (for the Sith admin)."""

    model = Club
    pk_url_kwarg = "club_id"
    fields = ["name", "parent"]
    template_name = "core/create.jinja"
    permission_required = "club.add_club"


class MembershipSetOldView(CanEditMixin, DetailView):
    """Set a membership as beeing old."""

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


class MembershipDeleteView(PermissionRequiredMixin, DeleteView):
    """Delete a membership (for admins only)."""

    model = Membership
    pk_url_kwarg = "membership_id"
    template_name = "core/delete_confirm.jinja"
    permission_required = "club.delete_membership"

    def get_success_url(self):
        return reverse_lazy("core:user_clubs", kwargs={"user_id": self.object.user.id})


class ClubMailingView(ClubTabsMixin, CanEditMixin, DetailFormView):
    """A list of mailing for a given club."""

    model = Club
    form_class = MailingForm
    pk_url_kwarg = "club_id"
    template_name = "club/mailing.jinja"
    current_tab = "mailing"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["club_id"] = self.object.id
        kwargs["user_id"] = self.request.user.id
        kwargs["mailings"] = self.object.mailings.all()
        return kwargs

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        mailings = list(self.object.mailings.all())
        kwargs["club"] = self.object
        kwargs["user"] = self.request.user
        kwargs["mailings"] = mailings
        kwargs["mailings_moderated"] = [m for m in mailings if m.is_moderated]
        kwargs["mailings_not_moderated"] = [m for m in mailings if not m.is_moderated]
        kwargs["form_actions"] = {
            "NEW_MALING": self.form_class.ACTION_NEW_MAILING,
            "NEW_SUBSCRIPTION": self.form_class.ACTION_NEW_SUBSCRIPTION,
            "REMOVE_SUBSCRIPTION": self.form_class.ACTION_REMOVE_SUBSCRIPTION,
        }
        return kwargs

    def add_new_mailing(self, cleaned_data) -> ValidationError | None:
        """Create a new mailing list from the form."""
        mailing = Mailing(
            club=self.object,
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
        """Add mailing subscriptions for each user given and/or for the specified email in form."""
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
        """Remove specified users from a mailing list."""
        fields = [
            val for key, val in cleaned_data.items() if key.startswith("removal_")
        ]
        for field in fields:
            for sub in field:
                sub.delete()

    def form_valid(self, form):
        resp = super().form_valid(form)

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
        return reverse("club:mailing", kwargs={"club_id": self.object.id})


class MailingDeleteView(CanEditMixin, DeleteView):
    model = Mailing
    template_name = "core/delete_confirm.jinja"
    pk_url_kwarg = "mailing_id"
    redirect_page = None

    def dispatch(self, request, *args, **kwargs):
        self.club_id = self.get_object().club.id
        return super().dispatch(request, *args, **kwargs)

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
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, **kwargs):
        return reverse_lazy("club:mailing", kwargs={"club_id": self.club_id})


class MailingAutoGenerationView(View):
    def dispatch(self, request, *args, **kwargs):
        self.mailing = get_object_or_404(Mailing, pk=kwargs["mailing_id"])
        if not request.user.can_edit(self.mailing):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        club = self.mailing.club
        self.mailing.subscriptions.all().delete()
        members = club.members.filter(
            role__gte=settings.SITH_CLUB_ROLES_ID["Board member"]
        ).exclude(end_date__lte=timezone.now())
        for member in members.all():
            MailingSubscription(user=member.user, mailing=self.mailing).save()
        return redirect("club:mailing", club_id=club.id)


class PosterListView(ClubTabsMixin, PosterListBaseView):
    """List communication posters."""

    current_tab = "posters"
    extra_context = {"app": "club"}

    def get_queryset(self):
        return super().get_queryset().filter(club=self.club.id)

    def get_object(self):
        return self.club


class PosterCreateView(ClubTabsMixin, PosterCreateBaseView):
    """Create communication poster."""

    current_tab = "posters"

    def get_success_url(self, **kwargs):
        return reverse_lazy("club:poster_list", kwargs={"club_id": self.club.id})

    def get_object(self, *args, **kwargs):
        return self.club


class PosterEditView(ClubTabsMixin, PosterEditBaseView):
    """Edit communication poster."""

    current_tab = "posters"
    extra_context = {"app": "club"}

    def get_success_url(self):
        return reverse_lazy("club:poster_list", kwargs={"club_id": self.club.id})


class PosterDeleteView(ClubTabsMixin, PosterDeleteBaseView):
    """Delete communication poster."""

    current_tab = "posters"

    def get_success_url(self):
        return reverse_lazy("club:poster_list", kwargs={"club_id": self.club.id})
