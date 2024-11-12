from collections.abc import Collection
from typing import Any

from django.contrib.staticfiles.storage import staticfiles_storage
from django.db.models import Model, QuerySet
from django.forms import Select, SelectMultiple
from ninja import ModelSchema
from pydantic import TypeAdapter

from core.models import Group, SithFile, User
from core.schemas import GroupSchema, SithFileSchema, UserProfileSchema


class AutoCompleteSelectMixin:
    component_name = "autocomplete-select"
    template_name = "core/widgets/autocomplete_select.jinja"
    model: type[Model] | None = None
    adapter: TypeAdapter[Collection[ModelSchema]] | None = None
    pk = "id"

    js = [
        "webpack/core/components/ajax-select-index.ts",
    ]
    css = [
        "webpack/core/components/ajax-select-index.css",
        "core/components/ajax-select.scss",
    ]

    def get_queryset(self, pks: Collection[Any]) -> QuerySet:
        return self.model.objects.filter(
            **{
                f"{self.pk}__in": [
                    pk
                    for pk in pks
                    if str(pk).isdigit()  # We filter empty values for create views
                ]
            }
        ).all()

    def __init__(self, attrs=None, choices=()):
        if self.is_ajax:
            choices = ()  # Avoid computing anything when in ajax mode
        super().__init__(attrs=attrs, choices=choices)

    @property
    def is_ajax(self):
        return self.adapter and self.model

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
            context["initial"] = self.adapter.dump_json(
                self.adapter.validate_python(
                    self.get_queryset(context["widget"]["value"])
                )
            ).decode("utf-8")
        return context


class AutoCompleteSelect(AutoCompleteSelectMixin, Select): ...


class AutoCompleteSelectMultiple(AutoCompleteSelectMixin, SelectMultiple): ...


class AutoCompleteSelectUser(AutoCompleteSelect):
    component_name = "user-ajax-select"
    model = User
    adapter = TypeAdapter(list[UserProfileSchema])


class AutoCompleteSelectMultipleUser(AutoCompleteSelectMultiple):
    component_name = "user-ajax-select"
    model = User
    adapter = TypeAdapter(list[UserProfileSchema])


class AutoCompleteSelectGroup(AutoCompleteSelect):
    component_name = "group-ajax-select"
    model = Group
    adapter = TypeAdapter(list[GroupSchema])


class AutoCompleteSelectMultipleGroup(AutoCompleteSelectMultiple):
    component_name = "group-ajax-select"
    model = Group
    adapter = TypeAdapter(list[GroupSchema])


class AutoCompleteSelectSithFile(AutoCompleteSelect):
    component_name = "sith-file-ajax-select"
    model = SithFile
    adapter = TypeAdapter(list[SithFileSchema])


class AutoCompleteSelectMultipleSithFile(AutoCompleteSelectMultiple):
    component_name = "sith-file-ajax-select"
    model = SithFile
    adapter = TypeAdapter(list[SithFileSchema])
