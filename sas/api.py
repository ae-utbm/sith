from typing import Any, Literal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.urls import reverse
from ninja import Body, File, Query
from ninja.security import SessionAuth
from ninja_extra import ControllerBase, api_controller, paginate, route
from ninja_extra.exceptions import NotFound, PermissionDenied
from ninja_extra.pagination import PageNumberPaginationExtra
from ninja_extra.schemas import PaginatedResponseSchema
from pydantic import NonNegativeInt

from api.auth import ApiKeyAuth
from api.permissions import (
    CanAccessLookup,
    CanEdit,
    CanView,
    IsInGroup,
    IsRoot,
)
from core.models import Notification, User
from core.schemas import UploadedImage
from sas.models import Album, PeoplePictureRelation, Picture
from sas.schemas import (
    AlbumAutocompleteSchema,
    AlbumFilterSchema,
    AlbumSchema,
    IdentifiedUserSchema,
    ModerationRequestSchema,
    PictureFilterSchema,
    PictureSchema,
)

IsSasAdmin = IsRoot | IsInGroup(settings.SITH_GROUP_SAS_ADMIN_ID)


@api_controller("/sas/album")
class AlbumController(ControllerBase):
    @route.get(
        "/search",
        response=PaginatedResponseSchema[AlbumSchema],
        url_name="search-album",
    )
    @paginate(PageNumberPaginationExtra, page_size=50)
    def fetch_album(self, filters: Query[AlbumFilterSchema]):
        """General-purpose album search."""
        return filters.filter(
            Album.objects.viewable_by(self.context.request.user).order_by("-date")
        )

    @route.get(
        "/autocomplete-search",
        response=PaginatedResponseSchema[AlbumAutocompleteSchema],
        auth=[ApiKeyAuth(), SessionAuth()],
        permissions=[CanAccessLookup],
    )
    @paginate(PageNumberPaginationExtra, page_size=50)
    def autocomplete_album(self, filters: Query[AlbumFilterSchema]):
        """Search route to use exclusively on autocomplete input fields.

        This route is separated from `GET /sas/album/search` because
        getting the path of an album may need an absurd amount of db queries.

        If you don't need the path of the albums,
        do NOT use this route.
        """
        return filters.filter(
            Album.objects.viewable_by(self.context.request.user).order_by("-date")
        )


@api_controller("/sas/picture")
class PicturesController(ControllerBase):
    @route.get("", response=PaginatedResponseSchema[PictureSchema], url_name="pictures")
    @paginate(PageNumberPaginationExtra, page_size=100)
    def fetch_pictures(self, filters: Query[PictureFilterSchema]):
        """Find pictures viewable by the user corresponding to the given filters.

        A user with an active subscription can see any picture, as long
        as it has been moderated and not asked for removal.
        An unsubscribed user can see the pictures he has been identified on
        (only the moderated ones, too).

        Notes:
            Trying to fetch the pictures of another user with this route
            while being unsubscribed will just result in an empty response.

        Notes:
            Unsubscribed users who are identified is not a rare case.
            They can be UTT students, faluchards from other schools,
            or even Richard Stallman (that ain't no joke,
            cf. https://ae.utbm.fr/user/32663/pictures/)
        """
        user: User = self.context.request.user
        return (
            filters.filter(Picture.objects.viewable_by(user))
            .distinct()
            .order_by("-parent__date", "date")
            .select_related("owner", "parent")
        )

    @route.post(
        "",
        permissions=[CanEdit],
        response={
            200: None,
            409: dict[Literal["detail"], dict[str, list[str]]],
            422: dict[Literal["detail"], list[dict[str, Any]]],
        },
        url_name="upload_picture",
    )
    def upload_picture(self, album_id: Body[int], picture: File[UploadedImage]):
        album = self.get_object_or_exception(Album, pk=album_id)
        user = self.context.request.user
        self_moderate = user.has_perm("sas.moderate_sasfile")
        new = Picture(
            parent=album,
            name=picture.name,
            file=picture,
            owner=user,
            is_moderated=self_moderate,
            is_folder=False,
            mime_type=picture.content_type,
        )
        if self_moderate:
            new.moderator = user
        try:
            new.generate_thumbnails()
            new.full_clean()
            new.save()
        except ValidationError as e:
            return self.create_response({"detail": dict(e)}, status_code=409)

    @route.get(
        "/{picture_id}/identified",
        permissions=[CanView],
        response=list[IdentifiedUserSchema],
        url_name="picture_identifications",
    )
    def fetch_identifications(self, picture_id: int):
        """Fetch the users that have been identified on the given picture."""
        picture = self.get_object_or_exception(Picture, pk=picture_id)
        return picture.people.viewable_by(self.context.request.user).select_related(
            "user"
        )

    @route.put("/{picture_id}/identified", permissions=[CanView])
    def identify_users(self, picture_id: NonNegativeInt, users: set[NonNegativeInt]):
        picture = self.get_object_or_exception(
            Picture.objects.select_related("parent"), pk=picture_id
        )
        db_users = list(User.objects.filter(id__in=users))
        if len(users) != len(db_users):
            raise NotFound
        already_identified = set(
            picture.people.filter(user_id__in=users).values_list("user_id", flat=True)
        )
        identified = [u for u in db_users if u.pk not in already_identified]
        relations = [
            PeoplePictureRelation(user=u, picture_id=picture_id) for u in identified
        ]
        PeoplePictureRelation.objects.bulk_create(relations)
        for u in identified:
            html_id = f"album-{picture.parent_id}"
            url = reverse(
                "sas:user_pictures", kwargs={"user_id": u.id}, fragment=html_id
            )
            Notification.objects.get_or_create(
                user=u,
                viewed=False,
                type="NEW_PICTURES",
                defaults={"url": url, "param": picture.parent.name},
            )

    @route.delete("/{picture_id}", permissions=[IsSasAdmin])
    def delete_picture(self, picture_id: int):
        self.get_object_or_exception(Picture, pk=picture_id).delete()

    @route.patch(
        "/{picture_id}/moderation",
        permissions=[IsSasAdmin],
        url_name="picture_moderate",
    )
    def moderate_picture(self, picture_id: int):
        """Mark a picture as moderated and remove its pending moderation requests."""
        picture = self.get_object_or_exception(Picture, pk=picture_id)
        picture.moderation_requests.all().delete()
        picture.is_moderated = True
        picture.moderator = self.context.request.user
        picture.asked_for_removal = False
        picture.save()

    @route.get(
        "/{picture_id}/moderation",
        permissions=[IsSasAdmin],
        response=list[ModerationRequestSchema],
        url_name="picture_moderation_requests",
    )
    def fetch_moderation_requests(self, picture_id: int):
        """Fetch the moderation requests issued on this picture."""
        picture = self.get_object_or_exception(Picture, pk=picture_id)
        return picture.moderation_requests.select_related("author")


@api_controller("/sas/relation", tags="User identification on SAS pictures")
class UsersIdentifiedController(ControllerBase):
    @route.delete("/{relation_id}")
    def delete_relation(self, relation_id: NonNegativeInt):
        """Untag a user from a SAS picture.

        Root and SAS admins can delete any picture identification.
        All other users can delete their own identification.
        """
        relation = self.get_object_or_exception(PeoplePictureRelation, pk=relation_id)
        user: User = self.context.request.user
        if (
            relation.user_id != user.id
            and not user.is_root
            and not user.is_in_group(pk=settings.SITH_GROUP_SAS_ADMIN_ID)
        ):
            raise PermissionDenied
        relation.delete()
