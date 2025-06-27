# Create your views here.

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, TemplateView, UpdateView

from club.models import Club
from core.auth.mixins import CanEditMixin
from reservation.forms import RoomCreateForm, RoomUpdateForm
from reservation.models import Room


class ReservationScheduleView(PermissionRequiredMixin, TemplateView):
    template_name = "reservation/schedule.jinja"
    permission_required = "reservation.view_room"


class RoomCreateView(SuccessMessageMixin, PermissionRequiredMixin, CreateView):
    form_class = RoomCreateForm
    template_name = "core/create.jinja"
    success_message = _("%(name)s was created successfully")
    permission_required = "reservation.add_room"

    def get_initial(self):
        init = super().get_initial()
        if "club" in self.request.GET:
            club_id = self.request.GET["club"]
            if club_id.isdigit() and int(club_id) > 0:
                init["club"] = Club.objects.filter(id=int(club_id)).first()
        return init


class RoomUpdateView(SuccessMessageMixin, CanEditMixin, UpdateView):
    model = Room
    pk_url_kwarg = "room_id"
    form_class = RoomUpdateForm
    template_name = "core/edit.jinja"
    success_message = _("%(name)s was updated successfully")

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {"request_user": self.request.user}

    def get_success_url(self):
        return self.request.path


class RoomDeleteView(PermissionRequiredMixin, DeleteView):
    model = Room
    pk_url_kwarg = "room_id"
    template_name = "core/delete_confirm.jinja"
    success_url = reverse_lazy("reservation:room_list")
    permission_required = "reservation.delete_room"
