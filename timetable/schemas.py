from typing import Annotated

from annotated_types import Ge, Le
from ninja import ModelSchema, Schema
from pydantic import Field

from timetable.models import Timetable, TimetableSlot


class TimetableSlotSchema(ModelSchema):
    weekday: TimetableSlot.WeekDay = Field(
        description=(
            f"{TimetableSlot.WeekDay.MONDAY} is monday, "
            f"{TimetableSlot.WeekDay.TUESDAY} is tuesday, etc."
        )
    )
    start_at: Annotated[int, Ge(0), Le(96)]
    end_at: Annotated[int, Ge(0), Le(96)]

    class Meta:
        model = TimetableSlot
        fields = ["start_at", "end_at", "week_group", "ue", "course_type", "room"]


class CreateTimetableSchema(Schema):
    is_viewable: bool
    slots: list[TimetableSlotSchema]


class TimetableSchema(ModelSchema):
    slots: list[TimetableSlotSchema]

    class Meta:
        model = Timetable
        fields = ["id", "semester"]
