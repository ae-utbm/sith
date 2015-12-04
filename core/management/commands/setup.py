import os
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from core.models import Group, User

class Command(BaseCommand):
    help = "Set up a new instance of the Sith AE"

    def add_arguments(self, parser):
        parser.add_argument('--prod', action="store_true")

    def handle(self, *args, **options):
        try:
            os.unlink(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'db.sqlite3'))
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
        if not options['prod']:
            print("Dev mode, adding some test data")
            u = User(username='skia', last_name="Kia", first_name="S'",
                     email="skia@git.an",
                     date_of_birth="1942-06-12T00:00:00+01:00",
                     is_superuser=True, is_staff=True)
            u.set_password("plop")
            u.save()

