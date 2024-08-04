from typing import Literal

from django.db.models import Q
from django.utils import html
from haystack.query import SearchQuerySet
from ninja import FilterSchema, ModelSchema, Schema
from pydantic import AliasPath, ConfigDict, Field, TypeAdapter
from pydantic.alias_generators import to_camel

from pedagogy.models import UV


class UtbmShortUvSchema(Schema):
    """Short representation of an UV in the UTBM API.

    Notes:
        This schema holds only the fields we actually need.
        The UTBM API returns more data than that.
    """

    model_config = ConfigDict(alias_generator=to_camel)

    code: str
    code_formation: str
    code_categorie: str | None
    code_langue: str
    ouvert_automne: bool
    ouvert_printemps: bool


class WorkloadSchema(Schema):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    code: Literal["TD", "TP", "CM", "THE", "TE"]
    nbh: int


class SemesterUvState(Schema):
    """The state of the UV during either autumn or spring semester"""

    model_config = ConfigDict(alias_generator=to_camel)

    responsable: str
    ouvert: bool


ShortUvList = TypeAdapter(list[UtbmShortUvSchema])


class UtbmFullUvSchema(Schema):
    """Long representation of an UV in the UTBM API."""

    model_config = ConfigDict(alias_generator=to_camel)

    code: str
    departement: str = "NA"
    libelle: str
    objectifs: str
    programme: str
    acquisition_competences: str
    acquisition_notions: str
    langue: str
    code_langue: str
    credits_ects: int
    activites: list[WorkloadSchema]
    respo_automne: str | None = Field(
        None, validation_alias=AliasPath("automne", "responsable")
    )
    respo_printemps: str | None = Field(
        None, validation_alias=AliasPath("printemps", "responsable")
    )


class SimpleUvSchema(ModelSchema):
    """Our minimal representation of an UV."""

    class Meta:
        model = UV
        fields = [
            "id",
            "title",
            "code",
            "credit_type",
            "semester",
            "department",
        ]


class UvSchema(ModelSchema):
    """Our complete representation of an UV"""

    class Meta:
        model = UV
        fields = [
            "id",
            "title",
            "code",
            "hours_THE",
            "hours_TD",
            "hours_TP",
            "hours_TE",
            "hours_CM",
            "credit_type",
            "semester",
            "language",
            "department",
            "credits",
            "manager",
            "skills",
            "key_concepts",
            "objectives",
            "program",
        ]


class UvFilterSchema(FilterSchema):
    search: str | None = Field(None, q="code__icontains")
    semester: set[Literal["AUTUMN", "SPRING"]] | None = None
    credit_type: set[Literal["CS", "TM", "EC", "OM", "QC"]] | None = Field(
        None, q="credit_type__in"
    )
    language: str = "FR"
    department: set[str] | None = Field(None, q="department__in")

    def filter_search(self, value: str | None) -> Q:
        """Special filter for the search text.

        It does a full text search if available.
        """
        if not value:
            return Q()

        if len(value) < 3 or (len(value) < 5 and any(c.isdigit() for c in value)):
            # Likely to be an UV code
            return Q(code__istartswith=value)

        qs = list(
            SearchQuerySet()
            .models(UV)
            .autocomplete(auto=html.escape(value))
            .values_list("pk", flat=True)
        )

        return Q(id__in=qs)

    def filter_semester(self, value: set[str] | None) -> Q:
        """Special filter for the semester.

        If either "SPRING" or "AUTUMN" is given, UV that are available
        during "AUTUMN_AND_SPRING" will be filtered.
        """
        if not value:
            return Q()
        value.add("AUTUMN_AND_SPRING")
        return Q(semester__in=value)
