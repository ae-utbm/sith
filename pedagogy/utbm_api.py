"""Set of functions to interact with the UTBM UE api."""

from typing import Iterator

import requests
from django.conf import settings
from django.utils.functional import cached_property

from pedagogy.schemas import ShortUeList, UeSchema, UtbmFullUeSchema, UtbmShortUeSchema


class UtbmApiClient(requests.Session):
    """A wrapper around `requests.Session` to perform requests to the UTBM UE API."""

    BASE_URL = settings.SITH_PEDAGOGY_UTBM_API
    _cache = {"short_ues": {}}

    @cached_property
    def current_year(self) -> int:
        """Fetch from the API the latest existing year"""
        url = f"{self.BASE_URL}/guides/fr"
        response = self.get(url)
        return response.json()[-1]["annee"]

    def fetch_short_ues(
        self, lang: str = "fr", year: int | None = None
    ) -> list[UtbmShortUeSchema]:
        """Get the list of UEs in their short format from the UTBM API"""
        if year is None:
            year = self.current_year
        if lang not in self._cache["short_ues"]:
            self._cache["short_ues"][lang] = {}
        if year not in self._cache["short_ues"][lang]:
            url = f"{self.BASE_URL}/uvs/{lang}/{year}"
            response = self.get(url)
            ues = ShortUeList.validate_json(response.content)
            self._cache["short_ues"][lang][year] = ues
        return self._cache["short_ues"][lang][year]

    def fetch_ues(
        self, lang: str = "fr", year: int | None = None
    ) -> Iterator[UeSchema]:
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
        shorts_ues = self.fetch_short_ues(lang, year)
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
            ue_url = f"{self.BASE_URL}/uv/{lang}/{year}/{ue.code}/{ue.code_formation}"
            response = requests.get(ue_url)
            full_ue = UtbmFullUeSchema.model_validate_json(response.content)
            yield make_clean_ue(ue, full_ue)

    def find_uu(self, lang: str, code: str, year: int | None = None) -> UeSchema | None:
        """Find an UE from the UTBM API."""
        # query the UE list
        if not year:
            year = self.current_year
        # the UTBM API has no way to fetch a single short ue,
        # and short ues contain infos that we need and are not
        # in the full ue schema, so we must fetch everything.
        short_ues = self.fetch_short_ues(lang, year)
        short_ue = next((ue for ue in short_ues if ue.code == code), None)
        if short_ue is None:
            return None

        # get detailed information about the UE
        ue_url = f"{self.BASE_URL}/uv/{lang}/{year}/{code}/{short_ue.code_formation}"
        response = requests.get(ue_url)
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
        }.get(short_ue.code_formation, "NA")

    match short_ue.ouvert_printemps, short_ue.ouvert_automne:
        case True, True:
            semester = "AUTUMN_AND_SPRING"
        case True, False:
            semester = "SPRING"
        case False, True:
            semester = "AUTUMN"
        case _:
            semester = "CLOSED"

    return UeSchema(
        title=full_ue.libelle or "",
        code=full_ue.code,
        credit_type=short_ue.code_categorie or "FREE",
        semester=semester,
        language=short_ue.code_langue.upper(),
        credits=full_ue.credits_ects,
        department=department,
        hours_THE=next((i.nbh for i in full_ue.activites if i.code == "THE"), 0) // 60,
        hours_TD=next((i.nbh for i in full_ue.activites if i.code == "TD"), 0) // 60,
        hours_TP=next((i.nbh for i in full_ue.activites if i.code == "TP"), 0) // 60,
        hours_TE=next((i.nbh for i in full_ue.activites if i.code == "TE"), 0) // 60,
        hours_CM=next((i.nbh for i in full_ue.activites if i.code == "CM"), 0) // 60,
        manager=full_ue.respo_automne or full_ue.respo_printemps or "",
        objectives=full_ue.objectifs or "",
        program=full_ue.programme or "",
        skills=full_ue.acquisition_competences or "",
        key_concepts=full_ue.acquisition_notions or "",
    )
