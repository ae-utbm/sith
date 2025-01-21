from django.conf import settings
from django.core.management import BaseCommand

from core.models import User
from pedagogy.models import UV
from pedagogy.schemas import UvSchema
from pedagogy.utbm_api import UtbmApiClient


class Command(BaseCommand):
    help = "Update the UV guide"

    def handle(self, *args, **options):
        seen_uvs: set[int] = set()
        root_user = User.objects.get(pk=settings.SITH_ROOT_USER_ID)
        with UtbmApiClient() as client:
            self.stdout.write(
                "Fetching UVs from the UTBM API.\n"
                "This may take a few minutes to complete."
            )
            for uv in client.fetch_uvs():
                db_uv = UV.objects.filter(code=uv.code).first()
                if db_uv is None:
                    db_uv = UV(code=uv.code, author=root_user)
                fields = list(UvSchema.model_fields.keys())
                fields.remove("id")
                fields.remove("code")
                for field in fields:
                    setattr(db_uv, field, getattr(uv, field))
                db_uv.save()
                # if it's a creation, django will set the id when saving,
                # so at this point, a db_uv will always have an id
                seen_uvs.add(db_uv.id)
        # UVs that are in database but have not been returned by the API
        # are considered as closed UEs
        UV.objects.exclude(id__in=seen_uvs).update(semester="CLOSED")
        self.stdout.write(self.style.SUCCESS("UV guide updated successfully"))
