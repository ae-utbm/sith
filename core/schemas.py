from ninja import ModelSchema, Schema

from core.models import User


class SimpleUserSchema(ModelSchema):
    """A schema with the minimum amount of information to represent a user."""

    class Meta:
        model = User
        fields = ["id", "nick_name", "first_name", "last_name"]


class MarkdownSchema(Schema):
    text: str
