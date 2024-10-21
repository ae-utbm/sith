from django.contrib.staticfiles.storage import staticfiles_storage
from django.db.models import Model
from django.forms import Select, SelectMultiple
from ninja import ModelSchema

from core.models import Group, SithFile, User
from core.schemas import GroupSchema, SithFileSchema, UserProfileSchema


class AutoCompleteSelectMixin:
    component_name = "autocomplete-select"
    template_name = "core/widgets/autocomplete_select.jinja"
    model: Model | None = None
    schema: ModelSchema | None = None
    pk = "id"

    js = [
        "webpack/core/components/ajax-select-index.ts",
    ]
    css = [
        "webpack/core/components/ajax-select-index.css",
        "core/components/ajax-select.scss",
    ]

    def __init__(self, attrs=None, choices=()):
        if self.is_ajax:
            choices = ()  # Avoid computing anything when in ajax mode
        super().__init__(attrs=attrs, choices=choices)

    @property
    def is_ajax(self):
        return self.model and self.schema

    def optgroups(self, name, value, attrs=None):
        """Don't create option groups when doing ajax"""
        if self.is_ajax:
            return []
        return super().optgroups(name, value, attrs=attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["attrs"]["autocomplete"] = "off"
        context["component"] = self.component_name
        context["statics"] = {
            "js": [staticfiles_storage.url(file) for file in self.js],
            "css": [staticfiles_storage.url(file) for file in self.css],
        }
        if self.is_ajax:
            context["selected"] = [
                self.schema.from_orm(obj).model_dump_json()
                for obj in self.model.objects.filter(
                    **{
                        f"{self.pk}__in": [
                            pk
                            for pk in context["widget"]["value"]
                            if str(
                                pk
                            ).isdigit()  # We filter empty values for create views
                        ]
                    }
                ).all()
            ]
        return context


class AutoCompleteSelect(AutoCompleteSelectMixin, Select): ...


class AutoCompleteSelectMultiple(AutoCompleteSelectMixin, SelectMultiple): ...


class AutoCompleteSelectUser(AutoCompleteSelect):
    component_name = "user-ajax-select"
    model = User
    schema = UserProfileSchema


class AutoCompleteSelectMultipleUser(AutoCompleteSelectMultiple):
    component_name = "user-ajax-select"
    model = User
    schema = UserProfileSchema


class AutoCompleteSelectGroup(AutoCompleteSelect):
    component_name = "group-ajax-select"
    model = Group
    schema = GroupSchema


class AutoCompleteSelectMultipleGroup(AutoCompleteSelectMultiple):
    component_name = "group-ajax-select"
    model = Group
    schema = GroupSchema


class AutoCompleteSelectSithFile(AutoCompleteSelect):
    component_name = "sith-file-ajax-select"
    model = SithFile
    schema = SithFileSchema


class AutoCompleteSelectMultipleSithFile(AutoCompleteSelectMultiple):
    component_name = "sith-file-ajax-select"
    model = SithFile
    schema = SithFileSchema
