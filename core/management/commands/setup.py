import os
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.conf import settings
from core.models import Group, User, Page, PageRev

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
                 date_of_birth="1942-06-12",
                 is_superuser=True, is_staff=True)
        u.set_password("plop")
        u.save()
        for g in settings.AE_GROUPS.values():
            Group(id=g['id'], name=g['name']).save()
        if not options['prod']:
            print("Dev mode, adding some test data")
            s = User(username='skia', last_name="Kia", first_name="S'",
                     email="skia@git.an",
                     date_of_birth="1942-06-12",
                     is_superuser=True, is_staff=True)
            s.set_password("plop")
            s.save()
            u = User(username='guy', last_name="Carlier", first_name="Guy",
                     email="guy@git.an",
                     date_of_birth="1942-06-12",
                     is_superuser=False, is_staff=False)
            u.set_password("plop")
            u.save()
            p = Page(name='Aide_sur_la_syntaxe')
            p.set_lock(s)
            p.save()
            PageRev(page=p, title="Aide sur la syntaxe", author=s, content="""
Cette page vise à documenter la syntaxe *Markdown* utilisée sur le site.
""").save()

