import os
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.conf import settings


class Command(BaseCommand):
    help = "Set up a new instance of the Sith AE"

    def add_arguments(self, parser):
        parser.add_argument('--prod', action="store_true")

    def handle(self, *args, **options):
        root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        try:
            os.mkdir(os.path.join(root_path)+'/data')
        except Exception as e:
            print(e)
        call_command('flush')
        call_command('migrate')
        if options['prod']:
            call_command('populate', '--prod')
        else:
            call_command('populate')
