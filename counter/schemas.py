from datetime import datetime

from ninja import FilterSchema, ModelSchema
from pydantic import Field

from core.models import User
from core.schemas import SimpleUserSchema
from counter.models import Counter, Permanency


class CounterSchema(ModelSchema):
    barmen_list: list[SimpleUserSchema]
    is_open: bool

    class Meta:
        model = Counter
        fields = ["id", "name", "type", "club", "products"]
        
class PermanencySchema(ModelSchema):
    class Meta:
        model = Permanency
        fields = ["user", "counter", "start", "end", "activity"]
        
class PermanencyFilterSchema(FilterSchema):
    start_date: datetime | None = Field(None, q="start__gte")
    end_date: datetime | None = Field(None, q="end__lte")
    barmen: set[int] | None = Field(None, q="user_id__in")
    counter: set[int] | None = Field(None, q="counter_id__in")
