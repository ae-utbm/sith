# This file contains all the views that concern the user model
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout as auth_logout, views
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist, ValidationError
from django.http import Http404
from django.views.generic.edit import UpdateView
from django.views.generic import ListView, DetailView, TemplateView, DeleteView
from django.forms.models import modelform_factory
from django.forms import CheckboxSelectMultiple
from django.template.response import TemplateResponse
from django.conf import settings
from django.views.generic.dates import YearMixin, MonthMixin

from django.utils import timezone
from datetime import timedelta, datetime, date
import logging

from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin, TabedViewMixin
from core.views.forms import RegisteringForm, UserPropForm, UserProfileForm, LoginForm, UserGodfathersForm
from core.models import User, SithFile
from club.models import Club
from subscription.models import Subscription

def login(request):
    """
    The login view

    Needs to be improve with correct handling of form exceptions
    """
    return views.login(request, template_name="core/login.jinja", authentication_form=LoginForm)

def logout(request):
    """
    The logout view
    """
    return views.logout_then_login(request)

def password_change(request):
    """
    Allows a user to change its password
    """
    return views.password_change(request, template_name="core/password_change.jinja", post_change_redirect=reverse("core:password_change_done"))

def password_change_done(request):
    """
    Allows a user to change its password
    """
    return views.password_change_done(request, template_name="core/password_change_done.jinja")

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
    return TemplateResponse(request, "core/password_change.jinja", {'form': form, 'target': user})

def password_reset(request):
    """
    Allows someone to enter an email adresse for resetting password
    """
    return views.password_reset(request,
                                template_name="core/password_reset.jinja",
                                email_template_name="core/password_reset_email.jinja",
                                post_reset_redirect="core:password_reset_done",
                               )

def password_reset_done(request):
    """
    Confirm that the reset email has been sent
    """
    return views.password_reset_done(request, template_name="core/password_reset_done.jinja")

def password_reset_confirm(request, uidb64=None, token=None):
    """
    Provide a reset password formular
    """
    return views.password_reset_confirm(request, uidb64=uidb64, token=token,
                                        post_reset_redirect="core:password_reset_complete",
                                        template_name="core/password_reset_confirm.jinja",
                                       )

def password_reset_complete(request):
    """
    Confirm the password has sucessfully been reset
    """
    return views.password_reset_complete(request,
                                         template_name="core/password_reset_complete.jinja",
                                        )

def register(request):
    context = {}
    if request.method == 'POST':
        form = RegisteringForm(request.POST)
        if form.is_valid():
            logging.debug("Registering "+form.cleaned_data['first_name']+form.cleaned_data['last_name'])
            u = form.save()
            context['user_registered'] = u
            context['tests'] = 'TEST_REGISTER_USER_FORM_OK'
            form = RegisteringForm()
        else:
            context['error'] = 'Erreur'
            context['tests'] = 'TEST_REGISTER_USER_FORM_FAIL'
    else:
        form = RegisteringForm()
    context['form'] = form.as_p()
    return render(request, "core/register.jinja", context)

class UserTabsMixin(TabedViewMixin):
    def get_tabs_title(self):
        return self.object.get_display_name()

    def get_list_of_tabs(self):
        tab_list = []
        tab_list.append({
                    'url': reverse('core:user_profile', kwargs={'user_id': self.object.id}),
                    'slug': 'infos',
                    'name': _("Infos"),
                    })
        tab_list.append({
                    'url': reverse('core:user_godfathers', kwargs={'user_id': self.object.id}),
                    'slug': 'godfathers',
                    'name': _("Godfathers"),
                    })
        if self.request.user == self.object:
            tab_list.append({
                        'url': reverse('core:user_tools'),
                        'slug': 'tools',
                        'name': _("Tools"),
                        })
        if self.request.user.can_edit(self.object):
            tab_list.append({
                        'url': reverse('core:user_edit', kwargs={'user_id': self.object.id}),
                        'slug': 'edit',
                        'name': _("Edit"),
                        })
        if self.request.user.can_view(self.object):
            tab_list.append({
                        'url': reverse('core:user_clubs', kwargs={'user_id': self.object.id}),
                        'slug': 'clubs',
                        'name': _("Clubs"),
                        })
        if self.request.user.is_owner(self.object):
            tab_list.append({
                        'url': reverse('core:user_groups', kwargs={'user_id': self.object.id}),
                        'slug': 'groups',
                        'name': _("Groups"),
                        })
        try:
            if (self.object.customer and (self.object == self.request.user
                or self.request.user.is_in_group(settings.SITH_GROUPS['accounting-admin']['name'])
                or self.request.user.is_in_group(settings.SITH_BAR_MANAGER['unix_name']+settings.SITH_BOARD_SUFFIX)
                or self.request.user.is_root)):
                tab_list.append({
                            'url': reverse('core:user_stats', kwargs={'user_id': self.object.id}),
                            'slug': 'stats',
                            'name': _("Stats"),
                            })
                tab_list.append({
                            'url': reverse('core:user_account', kwargs={'user_id': self.object.id}),
                            'slug': 'account',
                            'name': _("Account")+" (%s €)" % self.object.customer.amount,
                            })
        except: pass
        return tab_list

class UserView(UserTabsMixin, CanViewMixin, DetailView):
    """
    Display a user's profile
    """
    model = User
    pk_url_kwarg = "user_id"
    context_object_name = "profile"
    template_name = "core/user_detail.jinja"
    current_tab = 'infos'


def DeleteUserGodfathers(request, user_id, godfather_id, is_father):
    user = User.objects.get(id=user_id)
    if ((user == request.user) or
         request.user.is_root or
         request.user.is_board_member):
        ud = get_object_or_404(User, id=godfather_id)
        if is_father == "True":
            user.godfathers.remove(ud)
        else:
            user.godchildren.remove(ud)
    else:
        raise PermissionDenied
    return redirect('core:user_godfathers', user_id=user_id)


class UserGodfathersView(UserTabsMixin, CanViewMixin, DetailView):
    """
    Display a user's godfathers
    """
    model = User
    pk_url_kwarg = "user_id"
    context_object_name = "profile"
    template_name = "core/user_godfathers.jinja"
    current_tab = 'godfathers'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.form = UserGodfathersForm(request.POST)
        if self.form.is_valid() and self.form.cleaned_data['user'] != self.object:
            if self.form.cleaned_data['type'] == 'godfather':
                self.object.godfathers.add(self.form.cleaned_data['user'])
                self.object.save()
            else:
                self.object.godchildren.add(self.form.cleaned_data['user'])
                self.object.save()
            self.form = UserGodfathersForm()
        return super(UserGodfathersView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super(UserGodfathersView, self).get_context_data(**kwargs)
        try:
            kwargs['form'] = self.form
        except:
            kwargs['form'] = UserGodfathersForm()
        return kwargs

class UserStatsView(UserTabsMixin, CanViewMixin, DetailView):
    """
    Display a user's stats
    """
    model = User
    pk_url_kwarg = "user_id"
    context_object_name = "profile"
    template_name = "core/user_stats.jinja"
    current_tab = 'stats'

    def get_context_data(self, **kwargs):
        kwargs = super(UserStatsView, self).get_context_data(**kwargs)
        from counter.models import Counter, Product, Selling
        from django.db.models import Sum
        foyer = Counter.objects.filter(name="Foyer").first()
        mde = Counter.objects.filter(name="MDE").first()
        gommette = Counter.objects.filter(name="La Gommette").first()
        semester_start=Subscription.compute_start(d=date.today(), duration=3)
        kwargs['total_perm_time'] = sum([p.end-p.start for p in self.object.permanencies.exclude(end=None)], timedelta())
        kwargs['total_foyer_time'] = sum([p.end-p.start for p in self.object.permanencies.filter(counter=foyer).exclude(end=None)], timedelta())
        kwargs['total_mde_time'] = sum([p.end-p.start for p in self.object.permanencies.filter(counter=mde).exclude(end=None)], timedelta())
        kwargs['total_gommette_time'] = sum([p.end-p.start for p in self.object.permanencies.filter(counter=gommette).exclude(end=None)], timedelta())
        kwargs['total_foyer_buyings'] = sum([b.unit_price*b.quantity for b in
            self.object.customer.buyings.filter(counter=foyer, date__gte=semester_start)])
        kwargs['total_mde_buyings'] = sum([b.unit_price*b.quantity for b in self.object.customer.buyings.filter(counter=mde,
            date__gte=semester_start)])
        kwargs['total_gommette_buyings'] = sum([b.unit_price*b.quantity for b in
            self.object.customer.buyings.filter(counter=gommette, date__gte=semester_start)])
        kwargs['top_product'] = self.object.customer.buyings.values('product__name').annotate(
                product_sum=Sum('quantity')).exclude(product_sum=None).order_by('-product_sum').all()[:10]
        return kwargs

class UserMiniView(CanViewMixin, DetailView):
    """
    Display a user's profile
    """
    model = User
    pk_url_kwarg = "user_id"
    context_object_name = "profile"
    template_name = "core/user_mini.jinja"

class UserListView(ListView):
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
        from core.utils import resize_image
        from io import BytesIO
        from PIL import Image
        self.object = self.get_object()
        if self.object.profile_pict:
            raise ValidationError(_("User already has a profile picture"))
        f = request.FILES['new_profile_pict']
        parent = SithFile.objects.filter(parent=None, name="profiles").first()
        name = str(self.object.id) + "_profile.jpg" # Webcamejs uploads JPGs
        im = Image.open(BytesIO(f.read()))
        new_file = SithFile(parent=parent, name=name,
                file=resize_image(im, 400, f.content_type.split('/')[-1]),
                owner=self.object, is_folder=False, mime_type=f.content_type, size=f._size)
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

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.form = self.get_form()
        if self.form.instance.profile_pict and not (request.user.is_board_member or request.user.is_root):
            self.form.fields.pop('profile_pict', None)
        if self.form.instance.date_of_birth and not (request.user.is_board_member or request.user.is_root):
            self.form.fields.pop('date_of_birth')
        if self.form.instance.first_name and not (request.user.is_board_member or request.user.is_root):
            self.form.fields.pop('first_name')
        if self.form.instance.last_name and not (request.user.is_board_member or request.user.is_root):
            self.form.fields.pop('last_name')
        return self.render_to_response(self.get_context_data(form=self.form))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.form = self.get_form()
        if self.form.instance.profile_pict and not request.user.is_in_group(settings.SITH_MAIN_BOARD_GROUP):
            self.form.fields.pop('profile_pict', None)
        files = request.FILES.items()
        self.form.process(files)
        if request.user.is_authenticated() and request.user.can_edit(self.object) and self.form.is_valid():
            return super(UserUpdateProfileView, self).form_valid(self.form)
        return self.form_invalid(self.form)

    def get_context_data(self, **kwargs):
        kwargs = super(UserUpdateProfileView, self).get_context_data(**kwargs)
        kwargs['profile'] = self.form.instance
        kwargs['form'] = self.form
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

class UserUpdateGroupView(UserTabsMixin, CanEditPropMixin, UpdateView):
    """
    Edit a user's groups
    """
    model = User
    pk_url_kwarg = "user_id"
    template_name = "core/user_group.jinja"
    form_class = modelform_factory(User, fields=['groups'],
            widgets={'groups':CheckboxSelectMultiple})
    context_object_name = "profile"
    current_tab = "groups"

class UserToolsView(UserTabsMixin, TemplateView):
    """
    Displays the logged user's tools
    """
    template_name = "core/user_tools.jinja"
    current_tab = "tools"

    def get_context_data(self, **kwargs):
        self.object = self.request.user
        from launderette.models import Launderette
        kwargs = super(UserToolsView, self).get_context_data(**kwargs)
        kwargs['launderettes'] = Launderette.objects.all()
        kwargs['profile'] = self.request.user
        kwargs['object'] = self.request.user
        return kwargs

class UserAccountBase(UserTabsMixin, DetailView):
    """
    Base class for UserAccount
    """
    model = User
    pk_url_kwarg = "user_id"
    current_tab = "account"

    def dispatch(self, request, *arg, **kwargs): # Manually validates the rights
        res = super(UserAccountBase, self).dispatch(request, *arg, **kwargs)
        if (self.object == request.user
                or request.user.is_in_group(settings.SITH_GROUPS['accounting-admin']['name'])
                or request.user.is_in_group(settings.SITH_BAR_MANAGER['unix_name']+settings.SITH_BOARD_SUFFIX)
                or request.user.is_root):
            return res
        raise PermissionDenied

class UserAccountView(UserAccountBase):
    """
    Display a user's account
    """
    template_name = "core/user_account.jinja"

    def expense_by_month(self, obj, calc):
        stats = []

        for year in obj.datetimes('date', 'year', order='DESC'):
            stats.append([])
            i = 0
            for month in obj.filter(date__year=year.year).datetimes(
                'date', 'month', order='DESC'):
                q = obj.filter(
                    date__year=month.year,
                    date__month=month.month
                )
                stats[i].append((
                    sum([calc(p) for p in q]),
                    month
                ))
            i += 1
        return stats

    def invoices_calc(self, query):
        t = 0
        for it in query.items.all():
            t += it.quantity * it.product_unit_price
        return t

    def get_context_data(self, **kwargs):
        kwargs = super(UserAccountView, self).get_context_data(**kwargs)
        kwargs['profile'] = self.object
        try:
            kwargs['customer'] = self.object.customer
            kwargs['buyings_month'] = self.expense_by_month(
                self.object.customer.buyings,
                (lambda q: q.unit_price * q.quantity)
            )
            kwargs['invoices_month'] = self.expense_by_month(
                self.object.customer.user.invoices,
                self.invoices_calc
            )
            kwargs['refilling_month'] = self.expense_by_month(
                self.object.customer.refillings,
                (lambda q: q.amount)
            )
            kwargs['etickets'] = self.object.customer.buyings.exclude(product__eticket=None).all()
        except:
            pass
        return kwargs

class UserAccountDetailView(UserAccountBase, YearMixin, MonthMixin):
    """
    Display a user's account for month
    """
    template_name = "core/user_account_detail.jinja"

    def get_context_data(self, **kwargs):
        kwargs = super(UserAccountDetailView, self).get_context_data(**kwargs)
        kwargs['profile'] = self.object
        kwargs['year'] = self.get_year()
        kwargs['month'] = self.get_month()
        try:
            kwargs['customer'] = self.object.customer
        except:
            pass
        kwargs['tab'] = "account"
        return kwargs

