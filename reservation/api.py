from typing import Any, Literal

from django.core.exceptions import ValidationError
from ninja import Query
from ninja_extra import ControllerBase, api_controller, paginate, route
from ninja_extra.pagination import PageNumberPaginationExtra
from ninja_extra.schemas import PaginatedResponseSchema

from api.permissions import HasPerm
from reservation.models import ReservationSlot, Room
from reservation.schemas import (
    RoomFilterSchema,
    RoomSchema,
    SlotFilterSchema,
    SlotSchema,
    UpdateReservationSlotSchema,
)


@api_controller("/reservation/room")
class ReservableRoomController(ControllerBase):
    @route.get(
        "",
        response=list[RoomSchema],
        permissions=[HasPerm("reservation.view_room")],
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
        url_name="fetch_reservation_slots",
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
        url_name="change_reservation_slot",
    )
    def update_slot(self, slot_id: int, params: UpdateReservationSlotSchema):
        slot = self.get_object_or_exception(ReservationSlot, id=slot_id)
        slot.start_at = params.start_at
        slot.end_at = params.end_at
        try:
            slot.full_clean()
            slot.save()
        except ValidationError as e:
            return self.create_response({"detail": dict(e)}, status_code=409)
