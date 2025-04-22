from datetime import timedelta
from typing import Any, Literal

from django.core.exceptions import ValidationError
from ninja import Query
from ninja_extra import ControllerBase, api_controller, paginate, route
from ninja_extra.pagination import PageNumberPaginationExtra
from ninja_extra.schemas import PaginatedResponseSchema
from pydantic import FutureDatetime

from api.permissions import HasPerm
from reservation.models import ReservationSlot, Room
from reservation.schemas import (
    RoomFilterSchema,
    RoomSchema,
    SlotFilterSchema,
    SlotSchema,
)


@api_controller("/reservation/room")
class ReservableRoomController(ControllerBase):
    @route.get(
        "",
        response=list[RoomSchema],
        permissions=[HasPerm("reservation.viem_room")],
        url_name="fetch_reservable_rooms",
    )
    def fetch_rooms(self, filters: Query[RoomFilterSchema]):
        return filters.filter(Room.objects.select_related("club"))


@api_controller("/reservation/slot")
class ReservationSlotController(ControllerBase):
    @route.get(
        "",
        response=PaginatedResponseSchema[SlotSchema],
        permissions=[HasPerm("reservation.view_reservationslot")],
    )
    @paginate(PageNumberPaginationExtra)
    def fetch_slots(self, filters: Query[SlotFilterSchema]):
        return filters.filter(
            ReservationSlot.objects.select_related("author").order_by("start_at")
        )

    @route.patch(
        "/reservation/slot/{int:slot_id}",
        permissions=[HasPerm("reservation.change_reservationslot")],
        response={
            200: None,
            409: dict[Literal["detail"], dict[str, list[str]]],
            422: dict[Literal["detail"], list[dict[str, Any]]],
        },
    )
    def update_slot(self, start: FutureDatetime, duration: timedelta, slot_id: int):
        slot = self.get_object_or_exception(ReservationSlot, id=slot_id)
        slot.start_at = start
        slot.end_at = start + duration
        try:
            slot.full_clean()
            slot.save()
        except ValidationError as e:
            return self.create_response({"detail": dict(e)}, status_code=409)
