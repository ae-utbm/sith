# -*- coding:utf-8 -*
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

from django import forms
from django.views.generic import ListView, DetailView, TemplateView, View
from django.views.generic.edit import DeleteView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import UpdateView, CreateView
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as _t
from ajax_select.fields import AutoCompleteSelectField, AutoCompleteSelectMultipleField
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect

from core.views import (
    CanCreateMixin,
    CanViewMixin,
    CanEditMixin,
    CanEditPropMixin,
    TabedViewMixin,
    PageEditViewBase,
    DetailFormView,
)
from core.views.forms import SelectDate, SelectDateTime
from club.models import Club, Membership, Mailing, MailingSubscription
from sith.settings import SITH_MAXIMUM_FREE_ROLE
from counter.models import Selling, Counter
from core.models import User, PageRev
from com.views import (
    PosterListBaseView,
    PosterCreateBaseView,
    PosterEditBaseView,
    PosterDeleteBaseView,
)
from com.models import Poster

from django.conf import settings

# Custom forms


class ClubEditForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = ["address", "logo", "short_description"]

    def __init__(self, *args, **kwargs):
        super(ClubEditForm, self).__init__(*args, **kwargs)
        self.fields["short_description"].widget = forms.Textarea()


class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ("email", "club", "moderator")

    def __init__(self, *args, **kwargs):
        club_id = kwargs.pop("club_id", None)
        user_id = kwargs.pop("user_id", -1)  # Remember 0 is treated as None
        super(MailingForm, self).__init__(*args, **kwargs)
        if club_id:
            self.fields["club"].queryset = Club.objects.filter(id=club_id)
            self.fields["club"].initial = club_id
            self.fields["club"].widget = forms.HiddenInput()
        if user_id >= 0:
            self.fields["moderator"].queryset = User.objects.filter(id=user_id)
            self.fields["moderator"].initial = user_id
            self.fields["moderator"].widget = forms.HiddenInput()


class MailingSubscriptionForm(forms.ModelForm):
    class Meta:
        model = MailingSubscription
        fields = ("mailing", "user", "email")

    def __init__(self, *args, **kwargs):
        kwargs.pop("user_id", None)  # For standart interface
        club_id = kwargs.pop("club_id", None)
        super(MailingSubscriptionForm, self).__init__(*args, **kwargs)
        self.fields["email"].required = False
        if club_id:
            self.fields["mailing"].queryset = Mailing.objects.filter(
                club__id=club_id, is_moderated=True
            )

    user = AutoCompleteSelectField(
        "users", label=_("User"), help_text=None, required=False
    )


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


class ClubMemberForm(forms.Form):
    """
    Form handling the members of a club
    """

    error_css_class = "error"
    required_css_class = "required"

    users = AutoCompleteSelectMultipleField(
        "users",
        label=_("Users to add"),
        help_text=_("Search users to add (one or more)."),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.club = kwargs.pop("club")
        self.request_user = kwargs.pop("request_user")
        self.club_members = kwargs.pop("club_members", None)
        if not self.club_members:
            self.club_members = (
                self.club.members.filter(end_date=None).order_by("-role").all()
            )
        self.request_user_membership = self.club.get_membership_for(self.request_user)
        super(ClubMemberForm, self).__init__(*args, **kwargs)

        # Using a ModelForm binds too much the form with the model and we don't want that
        # We want the view to process the model creation since they are multiple users
        # We also want the form to handle bulk deletion
        self.fields.update(
            forms.fields_for_model(
                Membership,
                fields=("role", "start_date", "description"),
                widgets={"start_date": SelectDate},
            )
        )

        # Role is required only if users is specified
        self.fields["role"].required = False

        # Start date and description are never really required
        self.fields["start_date"].required = False
        self.fields["description"].required = False

        self.fields["users_old"] = forms.ModelMultipleChoiceField(
            User.objects.filter(
                id__in=[
                    ms.user.id
                    for ms in self.club_members
                    if ms.can_be_edited_by(
                        self.request_user, self.request_user_membership
                    )
                ]
            ).all(),
            label=_("Mark as old"),
            required=False,
            widget=forms.CheckboxSelectMultiple,
        )
        if not self.request_user.is_root:
            self.fields.pop("start_date")

    def clean_users(self):
        """
            Check that the user is not trying to add an user already in the club
            Also check that the user is valid and has a valid subscription
        """
        cleaned_data = super(ClubMemberForm, self).clean()
        users = []
        for user_id in cleaned_data["users"]:
            user = User.objects.filter(id=user_id).first()
            if not user:
                raise forms.ValidationError(
                    _("One of the selected users doesn't exist"), code="invalid"
                )
            if not user.is_subscribed:
                raise forms.ValidationError(
                    _("User must be subscriber to take part to a club"), code="invalid"
                )
            if self.club.get_membership_for(user):
                raise forms.ValidationError(
                    _("You can not add the same user twice"), code="invalid"
                )
            users.append(user)
        return users

    def clean(self):
        """
            Check user rights for adding an user
        """
        cleaned_data = super(ClubMemberForm, self).clean()

        if "start_date" in cleaned_data and not cleaned_data["start_date"]:
            # Drop start_date if allowed to edition but not specified
            cleaned_data.pop("start_date")

        if not cleaned_data.get("users"):
            # No user to add equals no check needed
            return cleaned_data

        if cleaned_data.get("role", "") == "":
            # Role is required if users exists
            self.add_error("role", _("You should specify a role"))
            return cleaned_data

        request_user = self.request_user
        membership = self.request_user_membership
        if not (
            cleaned_data["role"] <= SITH_MAXIMUM_FREE_ROLE
            or (membership is not None and membership.role >= cleaned_data["role"])
            or request_user.is_board_member
            or request_user.is_root
        ):
            raise forms.ValidationError(_("You do not have the permission to do that"))
        return cleaned_data


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
        kwargs["request_user"] = self.request_user
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
        self.request_user = request.user
        self.members = (
            self.get_object().members.filter(end_date=None).order_by("-role").all()
        )
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


class SellingsFormBase(forms.Form):
    begin_date = forms.DateTimeField(
        ["%Y-%m-%d %H:%M:%S"],
        label=_("Begin date"),
        required=False,
        widget=SelectDateTime,
    )
    end_date = forms.DateTimeField(
        ["%Y-%m-%d %H:%M:%S"],
        label=_("End date"),
        required=False,
        widget=SelectDateTime,
    )
    counter = forms.ModelChoiceField(
        Counter.objects.order_by("name").all(), label=_("Counter"), required=False
    )


class ClubSellingView(ClubTabsMixin, CanEditMixin, DetailView):
    """
    Sellings of a club
    """

    model = Club
    pk_url_kwarg = "club_id"
    template_name = "club/club_sellings.jinja"
    current_tab = "sellings"

    def get_form_class(self):
        kwargs = {
            "product": forms.ModelChoiceField(
                self.object.products.order_by("name").all(),
                label=_("Product"),
                required=False,
            )
        }
        return type("SellingsForm", (SellingsFormBase,), kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super(ClubSellingView, self).get_context_data(**kwargs)
        form = self.get_form_class()(self.request.GET)
        qs = Selling.objects.filter(club=self.object)
        if form.is_valid():
            if not len([v for v in form.cleaned_data.values() if v is not None]):
                qs = Selling.objects.filter(id=-1)
            if form.cleaned_data["begin_date"]:
                qs = qs.filter(date__gte=form.cleaned_data["begin_date"])
            if form.cleaned_data["end_date"]:
                qs = qs.filter(date__lte=form.cleaned_data["end_date"])
            if form.cleaned_data["counter"]:
                qs = qs.filter(counter=form.cleaned_data["counter"])
            if form.cleaned_data["product"]:
                qs = qs.filter(product__id=form.cleaned_data["product"].id)
            kwargs["result"] = qs.all().order_by("-id")
            kwargs["total"] = sum([s.quantity * s.unit_price for s in qs.all()])
            kwargs["total_quantity"] = sum([s.quantity for s in qs.all()])
            kwargs["benefit"] = kwargs["total"] - sum(
                [s.product.purchase_price for s in qs.exclude(product=None)]
            )
        else:
            kwargs["result"] = qs[:0]
        kwargs["form"] = form
        return kwargs


class ClubSellingCSVView(ClubSellingView):
    """
    Generate sellings in csv for a given period
    """

    def get(self, request, *args, **kwargs):
        import csv

        response = HttpResponse(content_type="text/csv")
        self.object = self.get_object()
        name = _("Sellings") + "_" + self.object.name + ".csv"
        response["Content-Disposition"] = "filename=" + name
        kwargs = self.get_context_data(**kwargs)
        writer = csv.writer(
            response, delimiter=";", lineterminator="\n", quoting=csv.QUOTE_ALL
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
        for o in kwargs["result"]:
            row = [o.date, o.counter]
            if o.seller:
                row.append(o.seller.get_display_name())
            else:
                row.append("")
            if o.customer:
                row.append(o.customer.user.get_display_name())
            else:
                row.append("")
            row = row + [
                o.label,
                o.quantity,
                o.quantity * o.unit_price,
                o.get_payment_method_display(),
            ]
            if o.product:
                row.append(o.product.selling_price)
                row.append(o.product.purchase_price)
                row.append(o.product.selling_price - o.product.purchase_price)
            else:
                row = row + ["", "", ""]
            writer.writerow(row)

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


class ClubCreateView(CanEditPropMixin, CreateView):
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


class ClubStatView(TemplateView):
    template_name = "club/stats.jinja"

    def get_context_data(self, **kwargs):
        kwargs = super(ClubStatView, self).get_context_data(**kwargs)
        kwargs["club_list"] = Club.objects.all()
        return kwargs


class ClubMailingView(ClubTabsMixin, ListView):
    """
    A list of mailing for a given club
    """

    action = None
    model = Mailing
    template_name = "club/mailing.jinja"
    current_tab = "mailing"

    def authorized(self):
        return (
            self.club.has_rights_in_club(self.user)
            or self.user.is_root
            or self.user.is_in_group(settings.SITH_GROUP_COM_ADMIN_ID)
        )

    def dispatch(self, request, *args, **kwargs):
        self.club = get_object_or_404(Club, pk=kwargs["club_id"])
        self.user = request.user
        self.object = self.club
        if not self.authorized():
            raise PermissionDenied
        self.member_form = MailingSubscriptionForm(club_id=self.club.id)
        self.mailing_form = MailingForm(club_id=self.club.id, user_id=self.user.id)
        return super(ClubMailingView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        res = super(ClubMailingView, self).get(request, *args, **kwargs)
        if self.action != "display":
            if self.action == "add_mailing":
                form = MailingForm
                model = Mailing
            elif self.action == "add_member":
                form = MailingSubscriptionForm
                model = MailingSubscription
            return MailingGenericCreateView.as_view(
                model=model, list_view=self, form_class=form
            )(request, *args, **kwargs)
        return res

    def get_queryset(self):
        return Mailing.objects.filter(club_id=self.club.id).all()

    def get_context_data(self, **kwargs):
        kwargs = super(ClubMailingView, self).get_context_data(**kwargs)
        kwargs["add_member"] = self.member_form
        kwargs["add_mailing"] = self.mailing_form
        kwargs["club"] = self.club
        kwargs["user"] = self.user
        kwargs["has_objects"] = len(kwargs["object_list"]) > 0
        return kwargs

    def get_object(self):
        return self.club


class MailingGenericCreateView(CreateView, SingleObjectMixin):
    """
    Create a new mailing list
    """

    list_view = None
    form_class = None

    def get_context_data(self, **kwargs):
        view_kwargs = self.list_view.get_context_data(**kwargs)
        for key, data in (
            super(MailingGenericCreateView, self).get_context_data(**kwargs).items()
        ):
            view_kwargs[key] = data
        view_kwargs[self.list_view.action] = view_kwargs["form"]
        return view_kwargs

    def get_form_kwargs(self):
        kwargs = super(MailingGenericCreateView, self).get_form_kwargs()
        kwargs["club_id"] = self.list_view.club.id
        kwargs["user_id"] = self.list_view.user.id
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        if not self.list_view.authorized():
            raise PermissionDenied
        self.template_name = self.list_view.template_name
        return super(MailingGenericCreateView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self, **kwargs):
        return reverse_lazy("club:mailing", kwargs={"club_id": self.list_view.club.id})


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


class MailingAutoCleanView(View):
    def dispatch(self, request, *args, **kwargs):
        self.mailing = get_object_or_404(Mailing, pk=kwargs["mailing_id"])
        if not request.user.can_edit(self.mailing):
            raise PermissionDenied
        return super(MailingAutoCleanView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.mailing.subscriptions.all().delete()
        return redirect("club:mailing", club_id=self.mailing.club.id)


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
