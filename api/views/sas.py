from typing import List
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response

from core.views import can_edit_prop
from core.models import User
from sas.models import Picture


def all_pictures_of_user(user: User) -> List[Picture]:
    return [
        relation.picture
        for relation in user.pictures.exclude(picture=None)
        .order_by("-picture__parent__date", "id")
        .select_related("picture__parent")
    ]


@api_view(["GET"])
@renderer_classes((JSONRenderer,))
def all_pictures_of_user_endpoint(request: Request, user: int):
    requested_user: User = get_object_or_404(User, pk=user)
    if not can_edit_prop(requested_user, request.user):
        raise PermissionDenied

    return Response(
        [
            {
                "name": f"{picture.parent.name} - {picture.name}",
                "date": picture.date,
                "author": str(picture.owner),
                "full_size_url": picture.get_download_url(),
                "compressed_url": picture.get_download_compressed_url(),
                "thumb_url": picture.get_download_thumb_url(),
            }
            for picture in all_pictures_of_user(requested_user)
        ]
    )
