"""Set of functions to interact with the UTBM UV api."""

import urllib

from django.conf import settings

from pedagogy.schemas import ShortUvList, UtbmFullUvSchema, UtbmShortUvSchema, UvSchema


def find_uv(lang, year, code) -> UvSchema | None:
    """Find an UV from the UTBM API."""
    # query the UV list
    base_url = settings.SITH_PEDAGOGY_UTBM_API
    uvs_url = f"{base_url}/uvs/{lang}/{year}"
    response = urllib.request.urlopen(uvs_url)
    uvs: list[UtbmShortUvSchema] = ShortUvList.validate_json(response.read())

    short_uv = next((uv for uv in uvs if uv.code == code), None)
    if short_uv is None:
        return None

    # get detailed information about the UV
    uv_url = f"{base_url}/uv/{lang}/{year}/{code}/{short_uv.code_formation}"
    response = urllib.request.urlopen(uv_url)
    full_uv = UtbmFullUvSchema.model_validate_json(response.read())
    return _make_clean_uv(short_uv, full_uv)


def _make_clean_uv(short_uv: UtbmShortUvSchema, full_uv: UtbmFullUvSchema) -> UvSchema:
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
        title=full_uv.libelle,
        code=full_uv.code,
        credit_type=short_uv.code_categorie,
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
        objectives=full_uv.objectifs,
        program=full_uv.programme,
        skills=full_uv.acquisition_competences,
        key_concepts=full_uv.acquisition_notions,
    )
