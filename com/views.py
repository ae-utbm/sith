from django.shortcuts import render
from django.views.generic import ListView, DetailView, RedirectView
from django.views.generic.edit import UpdateView, CreateView
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse, reverse_lazy
from django.core.exceptions import ValidationError
from django.utils import timezone
from django import forms

from datetime import timedelta

from com.models import Sith, News, NewsDate
from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin, TabedViewMixin
from core.views.forms import SelectDateTime
from club.models import Club


# Sith object

sith = Sith.objects.first

class ComTabsMixin(TabedViewMixin):
    def get_tabs_title(self):
        return _("Communication administration")

    def get_list_of_tabs(self):
        tab_list = []
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
        fields = ['type', 'title', 'club', 'summary', 'content', 'owner']
        widgets = {
                'owner': forms.HiddenInput,
                'type': forms.RadioSelect,
                }
    start_date = forms.DateTimeField(['%Y-%m-%d %H:%M:%S'], label=_("Start date"), widget=SelectDateTime, required=False)
    end_date = forms.DateTimeField(['%Y-%m-%d %H:%M:%S'], label=_("End date"), widget=SelectDateTime, required=False)
    until = forms.DateTimeField(['%Y-%m-%d %H:%M:%S'], label=_("Until"), widget=SelectDateTime, required=False)

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

class NewsEditView(UpdateView):
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

class NewsCreateView(CreateView):
    model = News
    form_class = NewsForm
    template_name = 'com/news_edit.jinja'

    def get_initial(self):
        init = {'owner': self.request.user}
        try:
            init['club'] = Club.objects.filter(id=self.request.GET['club']).first()
        except: pass
        return init

class NewsAdminListView(ListView):
    model = News
    template_name = 'com/news_admin_list.jinja'

class NewsListView(ListView):
    model = News
    template_name = 'com/news_list.jinja'

class NewsDetailView(DetailView):
    model = News
    template_name = 'com/news_detail.jinja'
    pk_url_kwarg = 'news_id'
