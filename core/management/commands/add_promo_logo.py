import pathlib

from django.core.management.base import BaseCommand
from PIL import Image

from sith.settings import BASE_DIR


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("numero", type=int)
        parser.add_argument("path", type=pathlib.Path)

    def handle(self, *args, **options):
        if options["path"].exists():
            path = pathlib.Path(
                f"{BASE_DIR}/core/static/core/img/promo_{options['numero']}.png"
            )
            try:
                with Image.open(options["path"]) as im:
                    im.resize((120, 120)).save(path, format="PNG")
            except IOError as ioe:
                self.stderr.write(ioe)
        else:
            self.stdout.write("file does not exist.")
