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

# This file contains all the views that concern the user model
import logging
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth import views
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import PermissionDenied, ValidationError
from django.forms import CheckboxSelectMultiple
from django.forms.models import modelform_factory
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
)
from django.views.generic.dates import MonthMixin, YearMixin
from django.views.generic.edit import UpdateView

from api.views.sas import all_pictures_of_user
from core.models import Gift, Preferences, SithFile, User
from core.views import (
    CanEditMixin,
    CanEditPropMixin,
    CanViewMixin,
    QuickNotifMixin,
    TabedViewMixin,
    UserIsLoggedMixin,
)
from core.views.forms import (
    GiftForm,
    LoginForm,
    RegisteringForm,
    UserGodfathersForm,
    UserProfileForm,
)
from counter.forms import StudentCardForm
from subscription.models import Subscription
from trombi.views import UserTrombiForm


class SithLoginView(views.LoginView):
    """
    The login View
    """

    template_name = "core/login.jinja"
    authentication_form = LoginForm
    form_class = PasswordChangeForm


class SithPasswordChangeView(views.PasswordChangeView):
    """
    Allows a user to change its password
    """

    template_name = "core/password_change.jinja"
    success_url = reverse_lazy("core:password_change_done")


class SithPasswordChangeDoneView(views.PasswordChangeDoneView):
    """
    Allows a user to change its password
    """

    template_name = "core/password_change_done.jinja"


def logout(request):
    """
    The logout view
    """
    return views.logout_then_login(request)


def password_root_change(request, user_id):
    """
    Allows a root user to change someone's password
    """
    if not request.user.is_root:
        raise PermissionDenied
    user = User.objects.filter(id=user_id).first()
    if not user:
        raise Http404("User not found")
    if request.method == "POST":
        form = views.SetPasswordForm(user=user, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect("core:password_change_done")
    else:
        form = views.SetPasswordForm(user=user)
    return TemplateResponse(
        request, "core/password_change.jinja", {"form": form, "target": user}
    )


class SithPasswordResetView(views.PasswordResetView):
    """
    Allows someone to enter an email adresse for resetting password
    """

    template_name = "core/password_reset.jinja"
    email_template_name = "core/password_reset_email.jinja"
    success_url = reverse_lazy("core:password_reset_done")


class SithPasswordResetDoneView(views.PasswordResetDoneView):
    """
    Confirm that the reset email has been sent
    """

    template_name = "core/password_reset_done.jinja"


class SithPasswordResetConfirmView(views.PasswordResetConfirmView):
    """
    Provide a reset password form
    """

    template_name = "core/password_reset_confirm.jinja"
    success_url = reverse_lazy("core:password_reset_complete")


class SithPasswordResetCompleteView(views.PasswordResetCompleteView):
    """
    Confirm the password has sucessfully been reset
    """

    template_name = "core/password_reset_complete.jinja"


def register(request):
    context = {}
    if request.method == "POST":
        form = RegisteringForm(request.POST)
        if form.is_valid():
            logging.debug(
                "Registering "
                + form.cleaned_data["first_name"]
                + form.cleaned_data["last_name"]
            )
            u = form.save()
            context["user_registered"] = u
            context["tests"] = "TEST_REGISTER_USER_FORM_OK"
            form = RegisteringForm()
        else:
            context["error"] = "Erreur"
            context["tests"] = "TEST_REGISTER_USER_FORM_FAIL"
    else:
        form = RegisteringForm()
    context["form"] = form.as_p()
    return render(request, "core/register.jinja", context)


class UserTabsMixin(TabedViewMixin):
    def get_tabs_title(self):
        return self.object.get_display_name()

    def get_list_of_tabs(self):
        user: User = self.object
        tab_list = [
            {
                "url": reverse("core:user_profile", kwargs={"user_id": user.id}),
                "slug": "infos",
                "name": _("Infos"),
            },
            {
                "url": reverse("core:user_godfathers", kwargs={"user_id": user.id}),
                "slug": "godfathers",
                "name": _("Family"),
            },
            {
                "url": reverse("core:user_pictures", kwargs={"user_id": user.id}),
                "slug": "pictures",
                "name": _("Pictures"),
            },
        ]
        if settings.SITH_ENABLE_GALAXY and self.request.user.was_subscribed:
            tab_list.append(
                {
                    "url": reverse("galaxy:user", kwargs={"user_id": user.id}),
                    "slug": "galaxy",
                    "name": _("Galaxy"),
                }
            )
        if self.request.user == user:
            tab_list.append(
                {"url": reverse("core:user_tools"), "slug": "tools", "name": _("Tools")}
            )
        if self.request.user.can_edit(user):
            tab_list.append(
                {
                    "url": reverse("core:user_edit", kwargs={"user_id": user.id}),
                    "slug": "edit",
                    "name": _("Edit"),
                }
            )
            tab_list.append(
                {
                    "url": reverse("core:user_prefs", kwargs={"user_id": user.id}),
                    "slug": "prefs",
                    "name": _("Preferences"),
                }
            )
        if self.request.user.can_view(user):
            tab_list.append(
                {
                    "url": reverse("core:user_clubs", kwargs={"user_id": user.id}),
                    "slug": "clubs",
                    "name": _("Clubs"),
                }
            )
        if self.request.user.is_owner(user):
            tab_list.append(
                {
                    "url": reverse("core:user_groups", kwargs={"user_id": user.id}),
                    "slug": "groups",
                    "name": _("Groups"),
                }
            )
        try:
            if user.customer and (
                user == self.request.user
                or self.request.user.is_in_group(
                    pk=settings.SITH_GROUP_ACCOUNTING_ADMIN_ID
                )
                or self.request.user.is_in_group(
                    name=settings.SITH_BAR_MANAGER["unix_name"]
                    + settings.SITH_BOARD_SUFFIX
                )
                or self.request.user.is_root
            ):
                tab_list.append(
                    {
                        "url": reverse("core:user_stats", kwargs={"user_id": user.id}),
                        "slug": "stats",
                        "name": _("Stats"),
                    }
                )
                tab_list.append(
                    {
                        "url": reverse(
                            "core:user_account", kwargs={"user_id": user.id}
                        ),
                        "slug": "account",
                        "name": _("Account") + " (%s €)" % user.customer.amount,
                    }
                )
        except:
            pass
        return tab_list


class UserView(UserTabsMixin, CanViewMixin, DetailView):
    """
    Display a user's profile
    """

    model = User
    pk_url_kwarg = "user_id"
    context_object_name = "profile"
    template_name = "core/user_detail.jinja"
    current_tab = "infos"

    def get_context_data(self, **kwargs):
        kwargs = super(UserView, self).get_context_data(**kwargs)
        kwargs["gift_form"] = GiftForm(
            user_id=self.object.id, initial={"user": self.object}
        )
        return kwargs


class UserPicturesView(UserTabsMixin, CanViewMixin, DetailView):
    """
    Display a user's pictures
    """

    model = User
    pk_url_kwarg = "user_id"
    context_object_name = "profile"
    template_name = "core/user_pictures.jinja"
    current_tab = "pictures"

    def get_context_data(self, **kwargs):
        kwargs = super(UserPicturesView, self).get_context_data(**kwargs)
        kwargs["albums"] = []
        kwargs["pictures"] = {}
        picture_qs = all_pictures_of_user(self.object)
        last_album = None
        for picture in picture_qs:
            album = picture.parent
            if album.id != last_album and album not in kwargs["albums"]:
                kwargs["albums"].append(album)
                kwargs["pictures"][album.id] = []
                last_album = album.id
            kwargs["pictures"][album.id].append(picture)
        return kwargs


def delete_user_godfather(request, user_id, godfather_id, is_father):
    user_is_admin = request.user.is_root or request.user.is_board_member
    if user_id != request.user.id and not user_is_admin:
        raise PermissionDenied()
    user = get_object_or_404(User, id=user_id)
    to_remove = get_object_or_404(User, id=godfather_id)
    if is_father:
        user.godfathers.remove(to_remove)
    else:
        user.godchildren.remove(to_remove)
    return redirect("core:user_godfathers", user_id=user_id)


class UserGodfathersView(UserTabsMixin, CanViewMixin, DetailView):
    """
    Display a user's godfathers
    """

    model = User
    pk_url_kwarg = "user_id"
    context_object_name = "profile"
    template_name = "core/user_godfathers.jinja"
    current_tab = "godfathers"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.form = UserGodfathersForm(request.POST)
        if self.form.is_valid() and self.form.cleaned_data["user"] != self.object:
            if self.form.cleaned_data["type"] == "godfather":
                self.object.godfathers.add(self.form.cleaned_data["user"])
                self.object.save()
            else:
                self.object.godchildren.add(self.form.cleaned_data["user"])
                self.object.save()
            self.form = UserGodfathersForm()
        return super(UserGodfathersView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super(UserGodfathersView, self).get_context_data(**kwargs)
        try:
            kwargs["form"] = self.form
        except:
            kwargs["form"] = UserGodfathersForm()
        return kwargs


class UserGodfathersTreeView(UserTabsMixin, CanViewMixin, DetailView):
    """
    Display a user's family tree
    """

    model = User
    pk_url_kwarg = "user_id"
    context_object_name = "profile"
    template_name = "core/user_godfathers_tree.jinja"
    current_tab = "godfathers"

    def get_context_data(self, **kwargs):
        kwargs = super(UserGodfathersTreeView, self).get_context_data(**kwargs)
        if "descent" in self.request.GET:
            kwargs["param"] = "godchildren"
        else:
            kwargs["param"] = "godfathers"
        kwargs["members_set"] = set()
        return kwargs


class UserGodfathersTreePictureView(CanViewMixin, DetailView):
    """
    Display a user's tree as a picture
    """

    model = User
    pk_url_kwarg = "user_id"

    def build_complex_graph(self):
        import pygraphviz as pgv

        self.depth = int(self.request.GET.get("depth", 4))
        if self.param == "godfathers":
            self.graph = pgv.AGraph(strict=False, directed=True, rankdir="BT")
        else:
            self.graph = pgv.AGraph(strict=False, directed=True)
        family = set()
        self.level = 1

        # Since the tree isn't very deep, we can build it recursively
        def crawl_family(user):
            if self.level > self.depth:
                return
            self.level += 1
            for u in user.__getattribute__(self.param).all():
                self.graph.add_edge(user.get_short_name(), u.get_short_name())
                if u not in family:
                    family.add(u)
                    crawl_family(u)
            self.level -= 1

        self.graph.add_node(self.object.get_short_name())
        family.add(self.object)
        crawl_family(self.object)

    def build_family_graph(self):
        import pygraphviz as pgv

        self.graph = pgv.AGraph(strict=False, directed=True)
        self.graph.add_node(self.object.get_short_name())
        for u in self.object.godfathers.all():
            self.graph.add_edge(u.get_short_name(), self.object.get_short_name())
        for u in self.object.godchildren.all():
            self.graph.add_edge(self.object.get_short_name(), u.get_short_name())

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if "descent" in self.request.GET:
            self.param = "godchildren"
        elif "ancestors" in self.request.GET:
            self.param = "godfathers"
        else:
            self.param = "family"

        if self.param == "family":
            self.build_family_graph()
        else:
            self.build_complex_graph()
        # Pimp the graph before display
        self.graph.node_attr["color"] = "lightblue"
        self.graph.node_attr["style"] = "filled"
        main_node = self.graph.get_node(self.object.get_short_name())
        main_node.attr["color"] = "sandybrown"
        main_node.attr["shape"] = "rect"
        if self.param == "godchildren":
            self.graph.graph_attr["label"] = _("Godchildren")
        elif self.param == "godfathers":
            self.graph.graph_attr["label"] = _("Family")
        else:
            self.graph.graph_attr["label"] = _("Family")
        img = self.graph.draw(format="png", prog="dot")
        return HttpResponse(img, content_type="image/png")


class UserStatsView(UserTabsMixin, CanViewMixin, DetailView):
    """
    Display a user's stats
    """

    model = User
    pk_url_kwarg = "user_id"
    context_object_name = "profile"
    template_name = "core/user_stats.jinja"
    current_tab = "stats"

    def dispatch(self, request, *arg, **kwargs):
        profile = self.get_object()

        if not hasattr(profile, "customer"):
            raise Http404

        if not (
            profile == request.user
            or request.user.is_in_group(pk=settings.SITH_GROUP_ACCOUNTING_ADMIN_ID)
            or request.user.is_in_group(
                name=settings.SITH_BAR_MANAGER["unix_name"] + settings.SITH_BOARD_SUFFIX
            )
            or request.user.is_root
        ):
            raise PermissionDenied

        return super(UserStatsView, self).dispatch(request, *arg, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super(UserStatsView, self).get_context_data(**kwargs)
        from django.db.models import Sum

        from counter.models import Counter

        foyer = Counter.objects.filter(name="Foyer").first()
        mde = Counter.objects.filter(name="MDE").first()
        gommette = Counter.objects.filter(name="La Gommette").first()
        semester_start = Subscription.compute_start(d=date.today(), duration=3)
        kwargs["total_perm_time"] = sum(
            [p.end - p.start for p in self.object.permanencies.exclude(end=None)],
            timedelta(),
        )
        kwargs["total_foyer_time"] = sum(
            [
                p.end - p.start
                for p in self.object.permanencies.filter(counter=foyer).exclude(
                    end=None
                )
            ],
            timedelta(),
        )
        kwargs["total_mde_time"] = sum(
            [
                p.end - p.start
                for p in self.object.permanencies.filter(counter=mde).exclude(end=None)
            ],
            timedelta(),
        )
        kwargs["total_gommette_time"] = sum(
            [
                p.end - p.start
                for p in self.object.permanencies.filter(counter=gommette).exclude(
                    end=None
                )
            ],
            timedelta(),
        )
        kwargs["total_foyer_buyings"] = sum(
            [
                b.unit_price * b.quantity
                for b in self.object.customer.buyings.filter(
                    counter=foyer, date__gte=semester_start
                )
            ]
        )
        kwargs["total_mde_buyings"] = sum(
            [
                b.unit_price * b.quantity
                for b in self.object.customer.buyings.filter(
                    counter=mde, date__gte=semester_start
                )
            ]
        )
        kwargs["total_gommette_buyings"] = sum(
            [
                b.unit_price * b.quantity
                for b in self.object.customer.buyings.filter(
                    counter=gommette, date__gte=semester_start
                )
            ]
        )
        kwargs["top_product"] = (
            self.object.customer.buyings.values("product__name")
            .annotate(product_sum=Sum("quantity"))
            .exclude(product_sum=None)
            .order_by("-product_sum")
            .all()[:10]
        )
        return kwargs


class UserMiniView(CanViewMixin, DetailView):
    """
    Display a user's profile
    """

    model = User
    pk_url_kwarg = "user_id"
    context_object_name = "profile"
    template_name = "core/user_mini.jinja"


class UserListView(ListView, CanEditPropMixin):
    """
    Displays the user list
    """

    model = User
    template_name = "core/user_list.jinja"


class UserUploadProfilePictView(CanEditMixin, DetailView):
    """
    Handle the upload of the profile picture taken with webcam in navigator
    """

    model = User
    pk_url_kwarg = "user_id"
    template_name = "core/user_edit.jinja"

    def post(self, request, *args, **kwargs):
        from io import BytesIO

        from PIL import Image

        from core.utils import resize_image

        self.object = self.get_object()
        if self.object.profile_pict:
            raise ValidationError(_("User already has a profile picture"))
        f = request.FILES["new_profile_pict"]
        parent = SithFile.objects.filter(parent=None, name="profiles").first()
        name = str(self.object.id) + "_profile.jpg"  # Webcamejs uploads JPGs
        im = Image.open(BytesIO(f.read()))
        new_file = SithFile(
            parent=parent,
            name=name,
            file=resize_image(im, 400, f.content_type.split("/")[-1]),
            owner=self.object,
            is_folder=False,
            mime_type=f.content_type,
            size=f.size,
        )
        new_file.file.name = name
        new_file.save()
        self.object.profile_pict = new_file
        self.object.save()
        return redirect("core:user_edit", user_id=self.object.id)


class UserUpdateProfileView(UserTabsMixin, CanEditMixin, UpdateView):
    """
    Edit a user's profile
    """

    model = User
    pk_url_kwarg = "user_id"
    template_name = "core/user_edit.jinja"
    form_class = UserProfileForm
    current_tab = "edit"
    edit_once = ["profile_pict", "date_of_birth", "first_name", "last_name"]
    board_only = []

    def remove_restricted_fields(self, request):
        """
        Removes edit_once and board_only fields
        """
        for i in self.edit_once:
            if getattr(self.form.instance, i) and not (
                request.user.is_board_member or request.user.is_root
            ):
                self.form.fields.pop(i, None)
        for i in self.board_only:
            if not (request.user.is_board_member or request.user.is_root):
                self.form.fields.pop(i, None)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.form = self.get_form()
        self.remove_restricted_fields(request)
        return self.render_to_response(self.get_context_data(form=self.form))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.form = self.get_form()
        self.remove_restricted_fields(request)
        files = request.FILES.items()
        self.form.process(files)
        if (
            request.user.is_authenticated
            and request.user.can_edit(self.object)
            and self.form.is_valid()
        ):
            return super(UserUpdateProfileView, self).form_valid(self.form)
        return self.form_invalid(self.form)

    def get_context_data(self, **kwargs):
        kwargs = super(UserUpdateProfileView, self).get_context_data(**kwargs)
        kwargs["profile"] = self.form.instance
        kwargs["form"] = self.form
        return kwargs


class UserClubView(UserTabsMixin, CanViewMixin, DetailView):
    """
    Display the user's club(s)
    """

    model = User
    context_object_name = "profile"
    pk_url_kwarg = "user_id"
    template_name = "core/user_clubs.jinja"
    current_tab = "clubs"


class UserPreferencesView(UserTabsMixin, CanEditMixin, UpdateView):
    """
    Edit a user's preferences
    """

    model = User
    pk_url_kwarg = "user_id"
    template_name = "core/user_preferences.jinja"
    form_class = modelform_factory(
        Preferences, fields=["receive_weekmail", "notify_on_click", "notify_on_refill"]
    )
    context_object_name = "profile"
    current_tab = "prefs"

    def get_object(self, queryset=None):
        user = get_object_or_404(User, pk=self.kwargs["user_id"])
        return user

    def get_form_kwargs(self):
        kwargs = super(UserPreferencesView, self).get_form_kwargs()
        pref = self.object.preferences
        kwargs.update({"instance": pref})
        return kwargs

    def get_context_data(self, **kwargs):
        kwargs = super(UserPreferencesView, self).get_context_data(**kwargs)

        if not (
            hasattr(self.object, "trombi_user") and self.request.user.trombi_user.trombi
        ):
            kwargs["trombi_form"] = UserTrombiForm()

        if hasattr(self.object, "customer"):
            kwargs["student_card_form"] = StudentCardForm()
        return kwargs


class UserUpdateGroupView(UserTabsMixin, CanEditPropMixin, UpdateView):
    """
    Edit a user's groups
    """

    model = User
    pk_url_kwarg = "user_id"
    template_name = "core/user_group.jinja"
    form_class = modelform_factory(
        User, fields=["groups"], widgets={"groups": CheckboxSelectMultiple}
    )
    context_object_name = "profile"
    current_tab = "groups"


class UserToolsView(QuickNotifMixin, UserTabsMixin, UserIsLoggedMixin, TemplateView):
    """
    Displays the logged user's tools
    """

    template_name = "core/user_tools.jinja"
    current_tab = "tools"

    def get_context_data(self, **kwargs):
        self.object = self.request.user
        from launderette.models import Launderette

        kwargs = super(UserToolsView, self).get_context_data(**kwargs)
        kwargs["launderettes"] = Launderette.objects.all()
        kwargs["profile"] = self.request.user
        kwargs["object"] = self.request.user
        return kwargs


class UserAccountBase(UserTabsMixin, DetailView):
    """
    Base class for UserAccount
    """

    model = User
    pk_url_kwarg = "user_id"
    current_tab = "account"

    def dispatch(self, request, *arg, **kwargs):  # Manually validates the rights
        res = super(UserAccountBase, self).dispatch(request, *arg, **kwargs)
        if (
            self.object == request.user
            or request.user.is_in_group(pk=settings.SITH_GROUP_ACCOUNTING_ADMIN_ID)
            or request.user.is_in_group(
                name=settings.SITH_BAR_MANAGER["unix_name"] + settings.SITH_BOARD_SUFFIX
            )
            or request.user.is_root
        ):
            return res
        raise PermissionDenied


class UserAccountView(UserAccountBase):
    """
    Display a user's account
    """

    template_name = "core/user_account.jinja"

    def expense_by_month(self, obj, calc):
        stats = []

        for year in obj.datetimes("date", "year", order="DESC"):
            stats.append([])
            i = 0
            for month in obj.filter(date__year=year.year).datetimes(
                "date", "month", order="DESC"
            ):
                q = obj.filter(date__year=month.year, date__month=month.month)
                stats[i].append({"sum": sum([calc(p) for p in q]), "date": month})
            i += 1
        return stats

    def invoices_calc(self, query):
        t = 0
        for it in query.items.all():
            t += it.quantity * it.product_unit_price
        return t

    def get_context_data(self, **kwargs):
        kwargs = super(UserAccountView, self).get_context_data(**kwargs)
        kwargs["profile"] = self.object
        try:
            kwargs["customer"] = self.object.customer
            kwargs["buyings_month"] = self.expense_by_month(
                self.object.customer.buyings, (lambda q: q.unit_price * q.quantity)
            )
            kwargs["invoices_month"] = self.expense_by_month(
                self.object.customer.user.invoices, self.invoices_calc
            )
            kwargs["refilling_month"] = self.expense_by_month(
                self.object.customer.refillings, (lambda q: q.amount)
            )
            kwargs["etickets"] = self.object.customer.buyings.exclude(
                product__eticket=None
            ).all()
        except Exception as e:
            print(repr(e))
        return kwargs


class UserAccountDetailView(UserAccountBase, YearMixin, MonthMixin):
    """
    Display a user's account for month
    """

    template_name = "core/user_account_detail.jinja"

    def get_context_data(self, **kwargs):
        kwargs = super(UserAccountDetailView, self).get_context_data(**kwargs)
        kwargs["profile"] = self.object
        kwargs["year"] = self.get_year()
        kwargs["month"] = self.get_month()
        try:
            kwargs["customer"] = self.object.customer
        except:
            pass
        kwargs["tab"] = "account"
        return kwargs


class GiftCreateView(CreateView):
    form_class = GiftForm
    template_name = "core/create.jinja"

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_board_member or request.user.is_root):
            raise PermissionDenied
        self.user = get_object_or_404(User, pk=kwargs["user_id"])
        return super(GiftCreateView, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        return {"user": self.user}

    def get_form_kwargs(self):
        kwargs = super(GiftCreateView, self).get_form_kwargs()
        kwargs["user_id"] = self.user.id
        return kwargs

    def get_success_url(self):
        return reverse_lazy("core:user_profile", kwargs={"user_id": self.user.id})


class GiftDeleteView(CanEditPropMixin, DeleteView):
    model = Gift
    pk_url_kwarg = "gift_id"
    template_name = "core/delete_confirm.jinja"

    def dispatch(self, request, *args, **kwargs):
        self.user = get_object_or_404(User, pk=kwargs["user_id"])
        return super(GiftDeleteView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy("core:user_profile", kwargs={"user_id": self.user.id})
