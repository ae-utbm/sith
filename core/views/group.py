from django.views.generic.edit import UpdateView
from django.views.generic import ListView

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
    form_class = GroupEditForm

