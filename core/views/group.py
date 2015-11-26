from django.views.generic.edit import UpdateView
from django.views.generic import ListView

from core.models import Group
from core.views.forms import GroupEditForm

class GroupListView(ListView):
    """
    Displays the group list
    """
    model = Group
    template_name = "core/group_list.html"

class GroupEditView(UpdateView):
    model = Group
    pk_url_kwarg = "group_id"
    template_name = "core/group_edit.html"
    form_class = GroupEditForm

