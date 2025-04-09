from django.core.management.base import BaseCommand
from PIL import Image


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--numero", type=int)
        parser.add_argument("--path", type=str)

    def handle(self, *args, **options):
        if options["path"] and options["numero"]:
            im = Image.open(options["path"]).resize((120, 120)).convert("RGBA")
            im.save(f"core/static/core/img/promo_{options['numero']}.png", format="PNG")
            im.close()
