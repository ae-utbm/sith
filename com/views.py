from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, RedirectView
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.views.generic.detail import SingleObjectMixin
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse, reverse_lazy
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from django.db.models import Max
from django import forms

from datetime import timedelta

from com.models import Sith, News, NewsDate, Weekmail, WeekmailArticle
from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin, TabedViewMixin, CanCreateMixin, QuickNotifMixin
from core.views.forms import SelectDateTime
from core.models import Notification, RealGroup
from club.models import Club


# Sith object

sith = Sith.objects.first

class ComTabsMixin(TabedViewMixin):
    def get_tabs_title(self):
        return _("Communication administration")

    def get_list_of_tabs(self):
        tab_list = []
        tab_list.append({
                    'url': reverse('com:weekmail'),
                    'slug': 'weekmail',
                    'name': _("Weekmail"),
                    })
        tab_list.append({
                    'url': reverse('com:index_edit'),
                    'slug': 'index',
                    'name': _("Index page"),
                    })
        tab_list.append({
                    'url': reverse('com:info_edit'),
                    'slug': 'info',
                    'name': _("Info message"),
                    })
        tab_list.append({
                    'url': reverse('com:alert_edit'),
                    'slug': 'alert',
                    'name': _("Alert message"),
                    })
        return tab_list

class ComEditView(ComTabsMixin, CanEditPropMixin, UpdateView):
    model = Sith
    template_name = 'core/edit.jinja'

    def get_object(self, queryset=None):
        return Sith.objects.first()

class AlertMsgEditView(ComEditView):
    fields = ['alert_msg']
    current_tab = "alert"
    success_url = reverse_lazy('com:alert_edit')

class InfoMsgEditView(ComEditView):
    fields = ['info_msg']
    current_tab = "info"
    success_url = reverse_lazy('com:info_edit')

class IndexEditView(ComEditView):
    fields = ['index_page']
    current_tab = "index"
    success_url = reverse_lazy('com:index_edit')

# News

class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ['type', 'title', 'club', 'summary', 'content', 'author']
        widgets = {
                'author': forms.HiddenInput,
                'type': forms.RadioSelect,
                }
    start_date = forms.DateTimeField(['%Y-%m-%d %H:%M:%S'], label=_("Start date"), widget=SelectDateTime, required=False)
    end_date = forms.DateTimeField(['%Y-%m-%d %H:%M:%S'], label=_("End date"), widget=SelectDateTime, required=False)
    until = forms.DateTimeField(['%Y-%m-%d %H:%M:%S'], label=_("Until"), widget=SelectDateTime, required=False)
    automoderation = forms.BooleanField(label=_("Automoderation"), required=False)

    def clean(self):
        self.cleaned_data = super(NewsForm, self).clean()
        if self.cleaned_data['type'] != "NOTICE":
            if not self.cleaned_data['start_date']:
                self.add_error('start_date', ValidationError(_("This field is required.")))
            if not self.cleaned_data['end_date']:
                self.add_error('end_date', ValidationError(_("This field is required.")))
            if self.cleaned_data['type'] == "WEEKLY" and not self.cleaned_data['until']:
                self.add_error('until', ValidationError(_("This field is required.")))
        return self.cleaned_data

    def save(self):
        ret = super(NewsForm, self).save()
        self.instance.dates.all().delete()
        if self.instance.type == "EVENT" or self.instance.type == "CALL":
            NewsDate(start_date=self.cleaned_data['start_date'],
                    end_date=self.cleaned_data['end_date'],
                    news=self.instance).save()
        elif self.instance.type == "WEEKLY":
            start_date = self.cleaned_data['start_date']
            end_date = self.cleaned_data['end_date']
            while start_date <= self.cleaned_data['until']:
                NewsDate(start_date=start_date,
                        end_date=end_date,
                        news=self.instance).save()
                start_date += timedelta(days=7)
                end_date += timedelta(days=7)
        return ret

class NewsEditView(CanEditMixin, UpdateView):
    model = News
    form_class = NewsForm
    template_name = 'com/news_edit.jinja'
    pk_url_kwarg = 'news_id'

    def get_initial(self):
        init = {}
        try:
            init['start_date'] = self.object.dates.order_by('id').first().start_date.strftime('%Y-%m-%d %H:%M:%S')
        except: pass
        try:
            init['end_date'] = self.object.dates.order_by('id').first().end_date.strftime('%Y-%m-%d %H:%M:%S')
        except: pass
        return init

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid() and not 'preview' in request.POST.keys():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        self.object = form.save()
        if form.cleaned_data['automoderation'] and self.request.user.is_in_group(settings.SITH_GROUP_COM_ADMIN_ID):
            self.object.moderator = self.request.user
            self.object.is_moderated = True
            self.object.save()
        else:
            self.object.is_moderated = False
            self.object.save()
            for u in RealGroup.objects.filter(id=settings.SITH_GROUP_COM_ADMIN_ID).first().users.all():
                if not u.notifications.filter(type="NEWS_MODERATION", viewed=False).exists():
                    Notification(user=u, url=reverse("com:news_detail", kwargs={'news_id': self.object.id}), type="NEWS_MODERATION").save()
        return super(NewsEditView, self).form_valid(form)

class NewsCreateView(CanCreateMixin, CreateView):
    model = News
    form_class = NewsForm
    template_name = 'com/news_edit.jinja'

    def get_initial(self):
        init = {'author': self.request.user}
        try:
            init['club'] = Club.objects.filter(id=self.request.GET['club']).first()
        except: pass
        return init

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid() and not 'preview' in request.POST.keys():
            return self.form_valid(form)
        else:
            self.object = form.instance
            return self.form_invalid(form)

    def form_valid(self, form):
        self.object = form.save()
        if form.cleaned_data['automoderation'] and self.request.user.is_in_group(settings.SITH_GROUP_COM_ADMIN_ID):
            self.object.moderator = self.request.user
            self.object.is_moderated = True
            self.object.save()
        else:
            for u in RealGroup.objects.filter(id=settings.SITH_GROUP_COM_ADMIN_ID).first().users.all():
                if not u.notifications.filter(type="NEWS_MODERATION", viewed=False).exists():
                    Notification(user=u, url=reverse("com:news_detail", kwargs={'news_id': self.object.id}), type="NEWS_MODERATION").save()
        return super(NewsCreateView, self).form_valid(form)

class NewsModerateView(CanEditMixin, SingleObjectMixin):
    model = News
    pk_url_kwarg = 'news_id'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.is_moderated = True
        self.object.moderator = request.user
        self.object.save()
        if 'next' in self.request.GET.keys():
            return redirect(self.request.GET['next'])
        return redirect('com:news_admin_list')

class NewsAdminListView(CanEditMixin, ListView):
    model = News
    template_name = 'com/news_admin_list.jinja'
    queryset = News.objects.filter(dates__end_date__gte=timezone.now()).distinct().order_by('id')

class NewsListView(CanViewMixin, ListView):
    model = News
    template_name = 'com/news_list.jinja'

    def get_context_data(self, **kwargs):
        kwargs = super(NewsListView, self).get_context_data(**kwargs)
        kwargs['NewsDate'] = NewsDate
        kwargs['timedelta'] = timedelta
        return kwargs

class NewsDetailView(CanViewMixin, DetailView):
    model = News
    template_name = 'com/news_detail.jinja'
    pk_url_kwarg = 'news_id'

# Weekmail

class WeekmailEditView(QuickNotifMixin, UpdateView):
    model = Weekmail
    template_name = 'com/weekmail.jinja'
    fields = ['title', 'intro', 'joke', 'protip', 'conclusion']
    success_url = reverse_lazy('com:weekmail')

    def get_object(self, queryset=None):
        weekmail = self.model.objects.filter(sent=False).order_by('-id').first()
        if not weekmail.title:
            now = timezone.now()
            weekmail.title = _("Weekmail of the ") + (now + timedelta(days=6 - now.weekday())).strftime('%d/%m/%Y')
        print(self.quick_notif_list)
        return weekmail

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        print(self.quick_notif_list)
        if 'up_article' in request.GET.keys():
            art = get_object_or_404(WeekmailArticle, id=request.GET['up_article'], weekmail=self.object)
            prev_art = self.object.articles.order_by('rank').filter(rank__lt=art.rank).last()
            if prev_art:
                art.rank, prev_art.rank = prev_art.rank, art.rank
                art.save()
                prev_art.save()
                self.quick_notif_list += ['qn_success']
        if 'down_article' in request.GET.keys():
            art = get_object_or_404(WeekmailArticle, id=request.GET['down_article'], weekmail=self.object)
            next_art = self.object.articles.order_by('rank').filter(rank__gt=art.rank).first()
            if next_art:
                art.rank, next_art.rank = next_art.rank, art.rank
                art.save()
                next_art.save()
                self.quick_notif_list += ['qn_success']
        if 'add_article' in request.GET.keys():
            art = get_object_or_404(WeekmailArticle, id=request.GET['add_article'], weekmail=None)
            art.weekmail = self.object
            art.rank = self.object.articles.aggregate(Max('rank'))['rank__max'] or 0
            art.rank += 1
            art.save()
            self.quick_notif_list += ['qn_success']
        if 'del_article' in request.GET.keys():
            art = get_object_or_404(WeekmailArticle, id=request.GET['del_article'], weekmail=self.object)
            art.weekmail = None
            art.rank = -1
            art.save()
            self.quick_notif_list += ['qn_success']
        print(self.quick_notif_list)
        return super(WeekmailEditView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Add orphan articles """
        kwargs = super(WeekmailEditView, self).get_context_data(**kwargs)
        kwargs['orphans'] = WeekmailArticle.objects.filter(weekmail=None)
        return kwargs

class WeekmailArticleEditView(QuickNotifMixin, UpdateView):
    """Edit an article"""
    model = WeekmailArticle
    fields = ['title', 'content']
    pk_url_kwarg = "article_id"
    template_name = 'core/edit.jinja'
    success_url = reverse_lazy('com:weekmail')
    quick_notif_url_arg = "qn_weekmail_article_edit"

class WeekmailArticleCreateView(QuickNotifMixin, CreateView):
    """Post an article"""
    model = WeekmailArticle
    fields = ['title', 'content']
    template_name = 'core/create.jinja'
    success_url = reverse_lazy('core:user_tools')
    quick_notif_url_arg = "qn_weekmail_new_article"

    def form_valid(self, form):
        club = get_object_or_404(Club, id=self.kwargs['club_id'])
        form.instance.club = club
        form.instance.author = self.request.user
        return super(WeekmailArticleCreateView, self).form_valid(form)

class WeekmailArticleDeleteView(DeleteView):
    """Delete an article"""
    model = WeekmailArticle
    template_name = 'core/delete_confirm.jinja'





