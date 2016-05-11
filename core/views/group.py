from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.views.generic import ListView
from django.core.urlresolvers import reverse_lazy

from core.models import RealGroup
from core.views.forms import GroupEditForm
from core.views import CanEditMixin

class GroupListView(CanEditMixin, ListView):
    """
    Displays the group list
    """
    model = RealGroup
    template_name = "core/group_list.jinja"

class GroupEditView(CanEditMixin, UpdateView):
    model = RealGroup
    pk_url_kwarg = "group_id"
    template_name = "core/group_edit.jinja"
    fields = ['name', 'description']

class GroupCreateView(CanEditMixin, CreateView):
    model = RealGroup
    template_name = "core/group_edit.jinja"
    fields = ['name', 'description']

class GroupDeleteView(CanEditMixin, DeleteView):
    model = RealGroup
    pk_url_kwarg = "group_id"
    template_name = "core/delete_confirm.jinja"
    success_url = reverse_lazy('core:group_list')
