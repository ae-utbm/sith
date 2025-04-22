from ninja import Query
from ninja_extra import ControllerBase, api_controller, paginate, route
from ninja_extra.pagination import PageNumberPaginationExtra
from ninja_extra.schemas import PaginatedResponseSchema

from core.auth.api_permissions import HasPerm
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
        return filters.filter(ReservationSlot.objects.select_related("author"))
