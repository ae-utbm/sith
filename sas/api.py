from django.conf import settings
from django.db.models import F
from ninja import Query
from ninja_extra import ControllerBase, api_controller, paginate, route
from ninja_extra.exceptions import PermissionDenied
from ninja_extra.pagination import PageNumberPaginationExtra
from ninja_extra.permissions import IsAuthenticated
from ninja_extra.schemas import PaginatedResponseSchema
from pydantic import NonNegativeInt

from core.models import User
from sas.models import PeoplePictureRelation, Picture
from sas.schemas import PictureFilterSchema, PictureSchema


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
        if not user.was_subscribed and filters.users_identified != {user.id}:
            # User can view any moderated picture if he/she is subscribed.
            # If not, he/she can view only the one he/she has been identified on
            raise PermissionDenied
        pictures = list(
            filters.filter(Picture.objects.viewable_by(user))
            .distinct()
            .order_by("-parent__date", "date")
            .annotate(album=F("parent__name"))
        )
        return pictures


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
