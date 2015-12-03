from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from core.models import Group, User

class Command(BaseCommand):
    help = "Set up a new instance of the Sith AE"

    def handle(self, *args, **options):
        try:
            # TODO: really remove the DB, to make sure all the tables and indexes are dropped
            call_command('flush', '--noinput', '--no-initial-data')
        except:
            pass
        call_command('migrate')
        u = User(username='root', last_name="", first_name="Bibou",
                 email="ae.info@utbm.fr",
                 date_of_birth="1942-06-12T00:00:00+01:00",
                 is_superuser=True, is_staff=True)
        u.set_password("plop")
        u.save()
        Group(name="root").save()
        # Just some example groups, only root is truly mandatory
        Group(name="bureau_restreint_ae").save()
        Group(name="bureau_ae").save()
        Group(name="membre_ae").save()

