from ninja import Query
from ninja_extra import ControllerBase, api_controller, route
from ninja_extra.exceptions import PermissionDenied
from ninja_extra.permissions import IsAuthenticated

from core.models import User
from sas.models import Picture
from sas.schemas import PictureFilterSchema, PictureSchema


@api_controller("/sas")
class SasController(ControllerBase):
    @route.get(
        "/picture",
        response=list[PictureSchema],
        permissions=[IsAuthenticated],
        url_name="pictures",
    )
    def fetch_pictures(self, filters: Query[PictureFilterSchema]):
        """Find pictures viewable by the user corresponding to the given filters.

        A user with an active subscription can see any picture, as long
        as it has been moderated and not asked for removal.
        An unsubscribed user can see the pictures he has been identified on
        (only the moderated ones, too)

        Notes:
            Trying to fetch the pictures of another user with this route
            while being unsubscribed will just result in an empty response.
        """
        user: User = self.context.request.user
        if not user.is_subscribed and filters.users_identified != {user.id}:
            # User can view any moderated picture if he/she is subscribed.
            # If not, he/she can view only the one he/she has been identified on
            raise PermissionDenied
        pictures = list(
            filters.filter(
                Picture.objects.filter(is_moderated=True, asked_for_removal=False)
            )
            .distinct()
            .order_by("-date")
        )
        for picture in pictures:
            picture.full_size_url = picture.get_download_url()
            picture.compressed_url = picture.get_download_compressed_url()
            picture.thumb_url = picture.get_download_thumb_url()
        return pictures
