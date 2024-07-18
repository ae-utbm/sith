from ninja import ModelSchema

from core.schemas import SimpleUserSchema
from counter.models import Counter


class CounterSchema(ModelSchema):
    barmen_list: list[SimpleUserSchema]
    is_open: bool

    class Meta:
        model = Counter
        fields = ["id", "name", "type", "club", "products"]
