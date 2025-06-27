from django.urls import path

from reservation.views import (
    RoomCreateView,
    RoomDeleteView,
    RoomUpdateView,
)

urlpatterns = [
    path("room/create/", RoomCreateView.as_view(), name="room_create"),
    path("room/<int:room_id>/edit", RoomUpdateView.as_view(), name="room_edit"),
    path("room/<int:room_id>/delete", RoomDeleteView.as_view(), name="room_delete"),
]
