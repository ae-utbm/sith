# -*- coding:utf-8 -*
#
# Copyright 2016,2017
# - Skia <skia@libskia.so>
#
# Ce fichier fait partie du site de l'Association des Étudiants de l'UTBM,
# http://ae.utbm.fr.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License a published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Sofware Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.
#
#

from rest_framework.response import Response
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import StaticHTMLRenderer, JSONRenderer
from rest_framework.views import APIView
from django.core.exceptions import PermissionDenied
from rest_framework import serializers
import urllib.request
import json

from core.templatetags.renderer import markdown
from pedagogy.views import CanCreateUVFunctionMixin


@api_view(["POST"])
@renderer_classes((StaticHTMLRenderer,))
def RenderMarkdown(request):
    """
        Render Markdown
    """
    try:
        data = markdown(request.POST["text"])
    except:
        data = "Error"
    return Response(data)


@api_view(["GET"])
@renderer_classes((JSONRenderer,))
def uv_endpoint(request):
    if not request.user.is_authenticated or not CanCreateUVFunctionMixin.can_create_uv(
        request.user
    ):
        raise PermissionDenied

    lang = "fr"

    params = request.query_params
    if "year" not in params or "code" not in params:
        raise serializers.ValidationError("Missing query parameter")

    uvs_url = "https://extranet1.utbm.fr/gpedago/api/guide/uvs/{lang}/{year}"
    response = urllib.request.urlopen(uvs_url.format(lang=lang, year=params["year"]))

    uvs = json.loads(response.read().decode("utf-8"))

    try:
        found = next(uv for uv in uvs if uv["code"] == params["code"])
    except StopIteration:
        # shouldn't be 404, rather something like 204
        return Response(status=404)

    uv_url = "https://extranet1.utbm.fr/gpedago/api/guide/uv/{lang}/{year}/{code}/{formation}"
    response = urllib.request.urlopen(
        uv_url.format(
            lang=lang,
            year=params["year"],
            code=params["code"],
            formation=found["codeFormation"],
        )
    )

    uv = json.loads(response.read().decode("utf-8"))

    res = {}

    res["credit_type"] = found["codeCategorie"]

    semesters = {
        (True, True): "AUTUMN_AND_SPRING",
        (True, False): "AUTOMN",
        (False, True): "SPRING",
    }
    res["semester"] = semesters.get(
        (found["ouvertAutomne"], found["ouvertPrintemps"]), "CLOSED"
    )

    langs = {"es": "SP", "en": "EN", "de": "DE"}
    res["language"] = langs.get(uv["codeLangue"], "FR")

    if uv["departement"] == "Pôle Humanités":
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
        res["department"] = departments.get(uv["codeFormation"], "NA")

    res["credits"] = uv["creditsEcts"]

    activities = ("CM", "TD", "TP", "THE", "TE")
    for activity in activities:
        res["hours_{}".format(activity)] = 0
    for activity in uv["activites"]:
        if activity["code"] in activities:
            res["hours_{}".format(activity["code"])] += activity["nbh"] // 60

    res["manager"] = uv["automne"]["responsable"]

    res["title"] = uv["libelle"]

    res["objectives"] = uv["objectifs"]
    res["program"] = uv["programme"]
    res["skills"] = uv["acquisitionCompetences"]
    res["key_concepts"] = uv["acquisitionNotions"]

    return Response(res)
