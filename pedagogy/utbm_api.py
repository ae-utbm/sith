"""Set of functions to interact with the UTBM UE api."""

from typing import Iterator

import requests
from django.conf import settings
from django.utils.functional import cached_property
from pydantic import TypeAdapter

from pedagogy.schemas import (
    FormationSchema,
    UeSchema,
    UtbmFullUeSchema,
    UtbmShortUeSchema,
)

FormationListSchema = TypeAdapter(list[FormationSchema])


class UtbmApiClient(requests.Session):
    """A wrapper around `requests.Session` to perform requests to the UTBM UE API."""

    BASE_URL = settings.SITH_PEDAGOGY_UTBM_API
    _cache = {"short_ues": {}}

    @cached_property
    def current_year(self) -> int:
        """Fetch from the API the latest existing year"""
        url = f"{self.BASE_URL}/guide/"
        response = self.get(url, {"langue": "fr"})
        return max(i["annee"] for i in response.json())

    @cached_property
    def formations(self) -> list[FormationSchema]:
        response = self.get(
            f"{self.BASE_URL}/formation/",
            {"langue": "fr", "annee_univ": self.current_year, "typeFormation": "ING"},
        )
        return FormationListSchema.validate_json(response.text, by_alias=True)

    def fetch_short_ues(self, year: int | None = None) -> list[UtbmShortUeSchema]:
        """Get the list of UEs in their short format from the UTBM API"""
        if year is None:
            year = self.current_year
        if year not in self._cache["short_ues"]:
            ues = []
            for formation in self.formations:
                response = self.get(
                    f"{self.BASE_URL}/ue/",
                    {
                        "langue": "fr",
                        "annee_univ": year,
                        "codeFormation": formation.code,
                    },
                )
                ues.extend(
                    [
                        UtbmShortUeSchema.model_validate({**ue, "formation": formation})
                        for ue in response.json()
                        if ue["codeCategorie"] is not None
                    ]
                )
            self._cache["short_ues"][year] = ues
        return self._cache["short_ues"][year]

    def fetch_ues(self, year: int | None = None) -> Iterator[UeSchema]:
        """Fetch all UEs from the UTBM API, parsed in a format that we can use.

        Warning:
            We need infos from the full ue schema, and the UTBM UE API
            has no route to get all of them at once.
            We must do one request per UE (for a total of around 730 UEs),
            which takes a lot of time.
            Hopefully, there seems to be no rate-limit, so an error
            in the middle of the process isn't likely to occur.
        """
        if year is None:
            year = self.current_year
        shorts_ues = self.fetch_short_ues(year)
        # When UEs are common to multiple branches (like most HUMA)
        # the UTBM API duplicates them for every branch.
        # We have no way in our db to link a UE to multiple formations,
        # so we just create a single UE, which formation is the one
        # of the first UE found in the list.
        # For example, if we have CC01 (TC), CC01 (IMSI) and CC01 (EDIM),
        # we will only keep CC01 (TC).
        unique_short_ues = {}
        for ue in shorts_ues:
            if ue.code not in unique_short_ues:
                unique_short_ues[ue.code] = ue
        for ue in unique_short_ues.values():
            if ue.lang.upper() != "FR":
                continue
            response = requests.get(
                f"{self.BASE_URL}/ue/{ue.code}",
                {
                    "langue": ue.lang,
                    "annee_univ": year,
                    "codeFormation": ue.formation.code,
                },
            )
            full_ue = UtbmFullUeSchema.model_validate_json(response.content)
            yield make_clean_ue(ue, full_ue)

    def find_ue(self, code: str, year: int | None = None) -> UeSchema | None:
        """Find a UE from the UTBM API."""
        if not year:
            year = self.current_year
        # the UTBM API has no way to fetch a single short ue,
        # and short ues contain infos that we need and are not
        # in the full ue schema, so we must fetch everything.
        short_ues = self.fetch_short_ues(year)
        short_ue = next((ue for ue in short_ues if ue.code == code), None)
        if short_ue is None:
            return None

        # get detailed information about the UE
        response = requests.get(
            f"{self.BASE_URL}/ue/{code}",
            {
                "langue": "fr",
                "annee_univ": year,
                "codeFormation": short_ue.formation.code,
            },
        )
        full_ue = UtbmFullUeSchema.model_validate_json(response.content)
        return make_clean_ue(short_ue, full_ue)


def make_clean_ue(short_ue: UtbmShortUeSchema, full_ue: UtbmFullUeSchema) -> UeSchema:
    """Cleans the data up so that it corresponds to our data representation.

    Some of the needed information are in the short ue schema, some
    other in the full ue schema.
    Thus we combine those information to obtain a data schema suitable
    for our needs.
    """
    if full_ue.departement == "Pôle Humanités":
        department = "HUMA"
    else:
        department = {
            "AL": "IMSI",
            "AE": "EE",
            "GI": "GI",
            "GC": "EE",
            "GM": "MC",
            "TC": "TC",
            "GP": "IMSI",
            "ED": "EDIM",
            "AI": "GI",
            "AM": "MC",
        }.get(short_ue.formation.code, "NA")

    match short_ue.open_spring, short_ue.open_autumn:
        case True, True:
            semester = "AUTUMN_AND_SPRING"
        case True, False:
            semester = "SPRING"
        case False, True:
            semester = "AUTUMN"
        case _:
            semester = "CLOSED"

    return UeSchema(
        title=full_ue.label or "",
        code=full_ue.code,
        credit_type=short_ue.category or "FREE",
        semester=semester,
        language=short_ue.lang.upper(),
        credits=full_ue.credits_ects,
        department=department,
        hours_THE=next((i.nbh for i in full_ue.activites if i.code == "THE"), 0) // 60,
        hours_TD=next((i.nbh for i in full_ue.activites if i.code == "TD"), 0) // 60,
        hours_TP=next((i.nbh for i in full_ue.activites if i.code == "TP"), 0) // 60,
        hours_TE=next((i.nbh for i in full_ue.activites if i.code == "TE"), 0) // 60,
        hours_CM=next((i.nbh for i in full_ue.activites if i.code == "CM"), 0) // 60,
        manager=full_ue.respo_automne or full_ue.respo_printemps or "",
        objectives=next(
            (i.value for i in full_ue.syllabus if i.label == "Objectifs"), ""
        ),
        program=next((i.value for i in full_ue.syllabus if i.label == "Programme"), ""),
        skills=next(
            (i.value for i in full_ue.syllabus if i.label == "Acquis d'apprentissage"),
            "",
        ),
        key_concepts=next(
            (i.value for i in full_ue.syllabus if i.label == "Notions-clés"),
            "",
        ),
    )
