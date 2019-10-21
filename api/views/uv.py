from rest_framework.response import Response
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from django.core.exceptions import PermissionDenied
from django.conf import settings
from rest_framework import serializers
import urllib.request
import json

from pedagogy.views import CanCreateUVFunctionMixin


@api_view(["GET"])
@renderer_classes((JSONRenderer,))
def uv_endpoint(request):
    if not CanCreateUVFunctionMixin.can_create_uv(request.user):
        raise PermissionDenied

    params = request.query_params
    if "year" not in params or "code" not in params:
        raise serializers.ValidationError("Missing query parameter")

    short_uv, full_uv = find_uv("fr", params["year"], params["code"])
    if short_uv is None or full_uv is None:
        return Response(status=204)

    return Response(make_clean_uv(short_uv, full_uv))


def find_uv(lang, year, code):
    """
        Uses the UTBM API to find an UV.
        short_uv is the UV entry in the UV list. It is returned as it contains
        information which are not in full_uv.
        full_uv is the detailed representation of an UV.
    """
    # query the UV list
    uvs_url = settings.SITH_PEDAGOGY_UTBM_API_UVS_URL
    response = urllib.request.urlopen(uvs_url.format(lang=lang, year=year))
    uvs = json.loads(response.read().decode("utf-8"))

    try:
        # find the first UV which matches the code
        short_uv = next(uv for uv in uvs if uv["code"] == code)
    except StopIteration:
        return (None, None)

    # get detailed information about the UV
    response = urllib.request.urlopen(
        settings.SITH_PEDAGOGY_UTBM_API_UV_URL.format(
            lang=lang, year=year, code=code, formation=short_uv["codeFormation"]
        )
    )
    full_uv = json.loads(response.read().decode("utf-8"))

    return (short_uv, full_uv)


def make_clean_uv(short_uv, full_uv):
    """
        Cleans the data up so that it corresponds to our data representation.
    """
    res = {}

    res["credit_type"] = short_uv["codeCategorie"]

    # probably wrong on a few UVs as we pick the first UV we find but
    # availability depends on the formation
    semesters = {
        (True, True): "AUTUMN_AND_SPRING",
        (True, False): "AUTUMN",
        (False, True): "SPRING",
    }
    res["semester"] = semesters.get(
        (short_uv["ouvertAutomne"], short_uv["ouvertPrintemps"]), "CLOSED"
    )

    langs = {"es": "SP", "en": "EN", "de": "DE"}
    res["language"] = langs.get(full_uv["codeLangue"], "FR")

    if full_uv["departement"] == "Pôle Humanités":
        res["department"] = "HUMA"
    else:
        departments = {
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
        }
        res["department"] = departments.get(full_uv["codeFormation"], "NA")

    res["credits"] = full_uv["creditsEcts"]

    activities = ("CM", "TD", "TP", "THE", "TE")
    for activity in activities:
        res["hours_{}".format(activity)] = 0
    for activity in full_uv["activites"]:
        if activity["code"] in activities:
            res["hours_{}".format(activity["code"])] += activity["nbh"] // 60

    # wrong if the manager changes depending on the semester
    semester = full_uv.get("automne", None)
    if not semester:
        semester = full_uv.get("printemps", {})
    res["manager"] = semester.get("responsable", "")

    res["title"] = full_uv["libelle"]

    res["objectives"] = full_uv["objectifs"]
    res["program"] = full_uv["programme"]
    res["skills"] = full_uv["acquisitionCompetences"]
    res["key_concepts"] = full_uv["acquisitionNotions"]

    return res
