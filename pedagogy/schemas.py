from typing import Annotated, Literal

from django.db.models import Q
from django.urls import reverse
from django.utils import html
from haystack.query import SearchQuerySet
from ninja import FilterLookup, FilterSchema, ModelSchema, Schema
from pydantic import AliasPath, ConfigDict, Field, TypeAdapter
from pydantic.alias_generators import to_camel

from pedagogy.models import UE


class UtbmShortUeSchema(Schema):
    """Short representation of an UE in the UTBM API.

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


class SemesterUeState(Schema):
    """The state of the UE during either autumn or spring semester"""

    model_config = ConfigDict(alias_generator=to_camel)

    responsable: str
    ouvert: bool


ShortUeList = TypeAdapter(list[UtbmShortUeSchema])


class UtbmFullUeSchema(Schema):
    """Long representation of an UE in the UTBM API."""

    model_config = ConfigDict(alias_generator=to_camel)

    code: str
    departement: str = "NA"
    libelle: str | None
    objectifs: str | None
    programme: str | None
    acquisition_competences: str | None
    acquisition_notions: str | None
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


class SimpleUeSchema(ModelSchema):
    """Our minimal representation of an UE."""

    class Meta:
        model = UE
        fields = [
            "id",
            "title",
            "code",
            "credit_type",
            "semester",
            "department",
        ]

    detail_url: str
    edit_url: str
    delete_url: str

    @staticmethod
    def resolve_detail_url(obj: UE) -> str:
        return reverse("pedagogy:ue_detail", kwargs={"ue_id": obj.id})

    @staticmethod
    def resolve_edit_url(obj: UE) -> str:
        return reverse("pedagogy:ue_update", kwargs={"ue_id": obj.id})

    @staticmethod
    def resolve_delete_url(obj: UE) -> str:
        return reverse("pedagogy:ue_delete", kwargs={"ue_id": obj.id})


class UeSchema(ModelSchema):
    """Our complete representation of an UE"""

    class Meta:
        model = UE
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


class UeFilterSchema(FilterSchema):
    search: Annotated[str | None, FilterLookup("code__icontains")] = None
    semester: set[Literal["AUTUMN", "SPRING"]] | None = None
    credit_type: Annotated[
        set[Literal["CS", "TM", "EC", "OM", "QC"]] | None,
        FilterLookup("credit_type__in"),
    ] = None
    language: str = "FR"
    department: Annotated[set[str] | None, FilterLookup("department__in")] = None

    def filter_search(self, value: str | None) -> Q:
        """Special filter for the search text.

        It does a full text search if available.
        """
        if not value:
            return Q()

        if len(value) < 3 or (len(value) < 5 and any(c.isdigit() for c in value)):
            # Likely to be an UE code
            return Q(code__istartswith=value)

        qs = list(
            SearchQuerySet()
            .models(UE)
            .autocomplete(auto=html.escape(value))
            .values_list("pk", flat=True)
        )

        return Q(id__in=qs)

    def filter_semester(self, value: set[str] | None) -> Q:
        """Special filter for the semester.

        If either "SPRING" or "AUTUMN" is given, UE that are available
        during "AUTUMN_AND_SPRING" will be filtered.
        """
        if not value:
            return Q()
        value.add("AUTUMN_AND_SPRING")
        return Q(semester__in=value)
