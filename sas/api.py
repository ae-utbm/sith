from django.conf import settings
from django.db.models import F
from django.urls import reverse
from ninja import Query
from ninja_extra import ControllerBase, api_controller, paginate, route
from ninja_extra.exceptions import NotFound, PermissionDenied
from ninja_extra.pagination import PageNumberPaginationExtra
from ninja_extra.permissions import IsAuthenticated
from ninja_extra.schemas import PaginatedResponseSchema
from pydantic import NonNegativeInt

from core.api_permissions import CanView, IsOwner
from core.models import Notification, User
from sas.models import PeoplePictureRelation, Picture
from sas.schemas import IdentifiedUserSchema, PictureFilterSchema, PictureSchema


@api_controller("/sas/picture")
class PicturesController(ControllerBase):
    @route.get(
        "",
        response=PaginatedResponseSchema[PictureSchema],
        permissions=[IsAuthenticated],
        url_name="pictures",
    )
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
            .select_related("owner")
            .annotate(album=F("parent__name"))
        )

    @route.get(
        "/{picture_id}/identified",
        permissions=[IsAuthenticated, CanView],
        response=list[IdentifiedUserSchema],
    )
    def fetch_identifications(self, picture_id: int):
        """Fetch the users that have been identified on the given picture."""
        picture = self.get_object_or_exception(Picture, pk=picture_id)
        return picture.people.select_related("user")

    @route.put("/{picture_id}/identified", permissions=[IsAuthenticated, CanView])
    def identify_users(self, picture_id: NonNegativeInt, users: set[NonNegativeInt]):
        picture = self.get_object_or_exception(Picture, pk=picture_id)
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
            Notification.objects.get_or_create(
                user=u,
                viewed=False,
                type="NEW_PICTURES",
                defaults={
                    "url": reverse("core:user_pictures", kwargs={"user_id": u.id})
                },
            )

    @route.delete("/{picture_id}", permissions=[IsOwner])
    def delete_picture(self, picture_id: int):
        self.get_object_or_exception(Picture, pk=picture_id).delete()

    @route.patch("/{picture_id}/moderate", permissions=[IsOwner])
    def moderate_picture(self, picture_id: int):
        picture = self.get_object_or_exception(Picture, pk=picture_id)
        picture.is_moderated = True
        picture.moderator = self.context.request.user
        picture.asked_for_removal = False
        picture.save()


@api_controller("/sas/relation", tags="User identification on SAS pictures")
class UsersIdentifiedController(ControllerBase):
    @route.delete("/{relation_id}", permissions=[IsAuthenticated])
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
