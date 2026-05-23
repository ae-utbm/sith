from datetime import datetime

from ninja import FilterSchema, ModelSchema, Schema
from pydantic import Field, FutureDatetime

from club.schemas import SimpleClubSchema
from core.schemas import SimpleUserSchema
from reservation.models import ReservationSlot, Room


class RoomFilterSchema(FilterSchema):
    club: set[int] | None = Field(None, q="club_id__in")


class RoomSchema(ModelSchema):
    class Meta:
        model = Room
        fields = ["id", "name", "description", "location"]

    club: SimpleClubSchema

    @staticmethod
    def resolve_location(obj: Room):
        return obj.get_location_display()


class SlotFilterSchema(FilterSchema):
    after: datetime = Field(default=None, q="end_at__gt")
    before: datetime = Field(default=None, q="start_at__lt")
    room: set[int] | None = None
    club: set[int] | None = None


class SlotSchema(ModelSchema):
    class Meta:
        model = ReservationSlot
        fields = ["id", "room", "comment"]

    start: datetime = Field(alias="start_at")
    end: datetime = Field(alias="end_at")
    author: SimpleUserSchema


class UpdateReservationSlotSchema(Schema):
    start_at: FutureDatetime
    end_at: FutureDatetime
