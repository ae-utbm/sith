from django.shortcuts import render
from django.views.generic.edit import UpdateView
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse, reverse_lazy

from com.models import Sith
from core.views import CanViewMixin, CanEditMixin, CanEditPropMixin, TabedViewMixin


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
