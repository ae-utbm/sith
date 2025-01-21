"""Set of functions to interact with the UTBM UV api."""

from typing import Iterator

import requests
from django.conf import settings
from django.utils.functional import cached_property

from pedagogy.schemas import ShortUvList, UtbmFullUvSchema, UtbmShortUvSchema, UvSchema


class UtbmApiClient(requests.Session):
    """A wrapper around `requests.Session` to perform requests to the UTBM UV API."""

    BASE_URL = settings.SITH_PEDAGOGY_UTBM_API
    _cache = {"short_uvs": {}}

    @cached_property
    def current_year(self) -> int:
        """Fetch from the API the latest existing year"""
        url = f"{self.BASE_URL}/guides/fr"
        response = self.get(url)
        return response.json()[-1]["annee"]

    def fetch_short_uvs(
        self, lang: str = "fr", year: int | None = None
    ) -> list[UtbmShortUvSchema]:
        """Get the list of UVs in their short format from the UTBM API"""
        if year is None:
            year = self.current_year
        if lang not in self._cache["short_uvs"]:
            self._cache["short_uvs"][lang] = {}
        if year not in self._cache["short_uvs"][lang]:
            url = f"{self.BASE_URL}/uvs/{lang}/{year}"
            response = self.get(url)
            uvs = ShortUvList.validate_json(response.content)
            self._cache["short_uvs"][lang][year] = uvs
        return self._cache["short_uvs"][lang][year]

    def fetch_uvs(
        self, lang: str = "fr", year: int | None = None
    ) -> Iterator[UvSchema]:
        """Fetch all UVs from the UTBM API, parsed in a format that we can use.

        Warning:
            We need infos from the full uv schema, and the UTBM UV API
            has no route to get all of them at once.
            We must do one request per UV (for a total of around 730 UVs),
            which takes a lot of time.
            Hopefully, there seems to be no rate-limit, so an error
            in the middle of the process isn't likely to occur.
        """
        if year is None:
            year = self.current_year
        shorts_uvs = self.fetch_short_uvs(lang, year)
        # When UVs are common to multiple branches (like most HUMA)
        # the UTBM API duplicates them for every branch.
        # We have no way in our db to link a UV to multiple formations,
        # so we just create a single UV, which formation is the one
        # of the first UV found in the list.
        # For example, if we have CC01 (TC), CC01 (IMSI) and CC01 (EDIM),
        # we will only keep CC01 (TC).
        unique_short_uvs = {}
        for uv in shorts_uvs:
            if uv.code not in unique_short_uvs:
                unique_short_uvs[uv.code] = uv
        for uv in unique_short_uvs.values():
            uv_url = f"{self.BASE_URL}/uv/{lang}/{year}/{uv.code}/{uv.code_formation}"
            response = requests.get(uv_url)
            full_uv = UtbmFullUvSchema.model_validate_json(response.content)
            yield make_clean_uv(uv, full_uv)

    def find_uv(self, lang: str, code: str, year: int | None = None) -> UvSchema | None:
        """Find an UV from the UTBM API."""
        # query the UV list
        if not year:
            year = self.current_year
        # the UTBM API has no way to fetch a single short uv,
        # and short uvs contain infos that we need and are not
        # in the full uv schema, so we must fetch everything.
        short_uvs = self.fetch_short_uvs(lang, year)
        short_uv = next((uv for uv in short_uvs if uv.code == code), None)
        if short_uv is None:
            return None

        # get detailed information about the UV
        uv_url = f"{self.BASE_URL}/uv/{lang}/{year}/{code}/{short_uv.code_formation}"
        response = requests.get(uv_url)
        full_uv = UtbmFullUvSchema.model_validate_json(response.content)
        return make_clean_uv(short_uv, full_uv)


def make_clean_uv(short_uv: UtbmShortUvSchema, full_uv: UtbmFullUvSchema) -> UvSchema:
    """Cleans the data up so that it corresponds to our data representation.

    Some of the needed information are in the short uv schema, some
    other in the full uv schema.
    Thus we combine those information to obtain a data schema suitable
    for our needs.
    """
    if full_uv.departement == "Pôle Humanités":
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
        }.get(short_uv.code_formation, "NA")

    match short_uv.ouvert_printemps, short_uv.ouvert_automne:
        case True, True:
            semester = "AUTUMN_AND_SPRING"
        case True, False:
            semester = "SPRING"
        case False, True:
            semester = "AUTUMN"
        case _:
            semester = "CLOSED"

    return UvSchema(
        title=full_uv.libelle or "",
        code=full_uv.code,
        credit_type=short_uv.code_categorie or "FREE",
        semester=semester,
        language=short_uv.code_langue.upper(),
        credits=full_uv.credits_ects,
        department=department,
        hours_THE=next((i.nbh for i in full_uv.activites if i.code == "THE"), 0) // 60,
        hours_TD=next((i.nbh for i in full_uv.activites if i.code == "TD"), 0) // 60,
        hours_TP=next((i.nbh for i in full_uv.activites if i.code == "TP"), 0) // 60,
        hours_TE=next((i.nbh for i in full_uv.activites if i.code == "TE"), 0) // 60,
        hours_CM=next((i.nbh for i in full_uv.activites if i.code == "CM"), 0) // 60,
        manager=full_uv.respo_automne or full_uv.respo_printemps or "",
        objectives=full_uv.objectifs or "",
        program=full_uv.programme or "",
        skills=full_uv.acquisition_competences or "",
        key_concepts=full_uv.acquisition_notions or "",
    )
