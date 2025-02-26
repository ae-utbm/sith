from io import BytesIO
from pathlib import Path
from typing import Annotated
from uuid import uuid4

import annotated_types
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse
from ninja import Query, UploadedFile
from ninja_extra import ControllerBase, api_controller, paginate, route
from ninja_extra.exceptions import PermissionDenied
from ninja_extra.pagination import PageNumberPaginationExtra
from ninja_extra.schemas import PaginatedResponseSchema
from PIL import Image, UnidentifiedImageError

from club.models import Mailing
from core.auth.api_permissions import CanAccessLookup, CanView, IsOldSubscriber
from core.models import Group, SithFile, User
from core.schemas import (
    FamilyGodfatherSchema,
    GroupSchema,
    MarkdownSchema,
    SithFileSchema,
    UploadedFileSchema,
    UserFamilySchema,
    UserFilterSchema,
    UserProfileSchema,
)
from core.templatetags.renderer import markdown


@api_controller("/markdown")
class MarkdownController(ControllerBase):
    @route.post("", url_name="markdown")
    def render_markdown(self, body: MarkdownSchema):
        """Convert the markdown text into html."""
        return HttpResponse(markdown(body.text), content_type="text/html")


@api_controller("/upload")
class UploadController(ControllerBase):
    @route.post("/images", response=UploadedFileSchema, permissions=[IsOldSubscriber])
    def upload_assets(self, file: UploadedFile):
        if file.content_type.split("/")[0] != "image":
            return self.create_response(
                message=f"{file.name} isn't a file image", status_code=400
            )

        def convert_image(file: UploadedFile) -> ContentFile:
            content = BytesIO()
            Image.open(BytesIO(file.read())).save(
                fp=content, format="webp", optimize=True
            )
            return ContentFile(content.getvalue())

        try:
            converted = convert_image(file)
        except UnidentifiedImageError:
            return self.create_response(
                message=f"{file.name} can't be processed", status_code=400
            )

        with transaction.atomic():
            parent = SithFile.objects.filter(parent=None, name="upload").first()
            if parent is None:
                root = User.objects.get(id=settings.SITH_ROOT_USER_ID)
                parent = SithFile.objects.create(
                    parent=None,
                    name="upload",
                    owner=root,
                )
            image = SithFile(
                parent=parent,
                name=f"{Path(file.name).stem}_{uuid4()}.webp",
                file=converted,
                owner=self.context.request.user,
                is_folder=False,
                mime_type="img/webp",
                size=converted.size,
                moderator=self.context.request.user,
                is_moderated=True,
            )
            image.file.name = image.name
            image.clean()
            image.save()
            image.view_groups.add(
                Group.objects.filter(id=settings.SITH_GROUP_PUBLIC_ID).first()
            )
            image.save()
        return image


@api_controller("/mailings")
class MailingListController(ControllerBase):
    @route.get("", response=str)
    def fetch_mailing_lists(self, key: str):
        if key != settings.SITH_MAILING_FETCH_KEY:
            raise PermissionDenied
        mailings = Mailing.objects.filter(
            is_moderated=True, club__is_active=True
        ).prefetch_related("subscriptions")
        data = "\n".join(m.fetch_format() for m in mailings)
        return data


@api_controller("/user", permissions=[CanAccessLookup])
class UserController(ControllerBase):
    @route.get("", response=list[UserProfileSchema])
    def fetch_profiles(self, pks: Query[set[int]]):
        return User.objects.filter(pk__in=pks)

    @route.get(
        "/search",
        response=PaginatedResponseSchema[UserProfileSchema],
        url_name="search_users",
    )
    @paginate(PageNumberPaginationExtra, page_size=20)
    def search_users(self, filters: Query[UserFilterSchema]):
        return filters.filter(
            User.objects.order_by(F("last_login").desc(nulls_last=True))
        )


@api_controller("/file")
class SithFileController(ControllerBase):
    @route.get(
        "/search",
        response=PaginatedResponseSchema[SithFileSchema],
        permissions=[CanAccessLookup],
    )
    @paginate(PageNumberPaginationExtra, page_size=50)
    def search_files(self, search: Annotated[str, annotated_types.MinLen(1)]):
        return SithFile.objects.filter(is_in_sas=False).filter(name__icontains=search)


@api_controller("/group")
class GroupController(ControllerBase):
    @route.get(
        "/search",
        response=PaginatedResponseSchema[GroupSchema],
        permissions=[CanAccessLookup],
    )
    @paginate(PageNumberPaginationExtra, page_size=50)
    def search_group(self, search: Annotated[str, annotated_types.MinLen(1)]):
        return Group.objects.filter(name__icontains=search).values()


DepthValue = Annotated[int, annotated_types.Ge(0), annotated_types.Le(10)]
DEFAULT_DEPTH = 4


@api_controller("/family")
class FamilyController(ControllerBase):
    @route.get(
        "/{user_id}",
        permissions=[CanView],
        response=UserFamilySchema,
        url_name="family_graph",
    )
    def get_family_graph(
        self,
        user_id: int,
        godfathers_depth: DepthValue = DEFAULT_DEPTH,
        godchildren_depth: DepthValue = DEFAULT_DEPTH,
    ):
        user: User = self.get_object_or_exception(User, pk=user_id)

        relations = user.get_family(godfathers_depth, godchildren_depth)
        if not relations:
            # If the user has no relations, return only the user
            # He is alone in its family, but the family exists nonetheless
            return {"users": [user], "relationships": []}

        user_ids = {r.from_user_id for r in relations} | {
            r.to_user_id for r in relations
        }
        return {
            "users": User.objects.filter(id__in=user_ids).distinct(),
            "relationships": (
                [
                    FamilyGodfatherSchema(
                        godchild=r.from_user_id, godfather=r.to_user_id
                    )
                    for r in relations
                ]
            ),
        }
