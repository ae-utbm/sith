from django.conf import settings
from django.core.management import BaseCommand

from core.models import User
from pedagogy.models import UE
from pedagogy.schemas import UeSchema
from pedagogy.utbm_api import UtbmApiClient


class Command(BaseCommand):
    help = "Update the UE guide"

    def handle(self, *args, **options):
        seen_ues: set[int] = set()
        root_user = User.objects.get(pk=settings.SITH_ROOT_USER_ID)
        with UtbmApiClient() as client:
            self.stdout.write(
                "Fetching UEs from the UTBM API.\n"
                "This may take a few minutes to complete."
            )
            for ue in client.fetch_ues():
                db_ue = UE.objects.filter(code=ue.code).first()
                if db_ue is None:
                    db_ue = UE(code=ue.code, author=root_user)
                fields = list(UeSchema.model_fields.keys())
                fields.remove("id")
                fields.remove("code")
                for field in fields:
                    setattr(db_ue, field, getattr(ue, field))
                db_ue.save()
                # if it's a creation, django will set the id when saving,
                # so at this point, a db_ue will always have an id
                seen_ues.add(db_ue.id)
        # UEs that are in database but have not been returned by the API
        # are considered as closed UEs
        UE.objects.exclude(id__in=seen_ues).update(semester="CLOSED")
        self.stdout.write(self.style.SUCCESS("UE guide updated successfully"))
