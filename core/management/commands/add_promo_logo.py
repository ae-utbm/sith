import pathlib

from django.core.management.base import BaseCommand
from PIL import Image

from sith.settings import BASE_DIR


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("numero", type=int)
        parser.add_argument("path", type=pathlib.Path)
        parser.add_argument("-f", "--force", action="store_true")

    def handle(self, *args, **options):
        if options["path"].exists():
            dest_path = pathlib.Path(
                f"{BASE_DIR}/core/static/core/img/promo_{options['numero']}.png"
            )
            if dest_path.exists() and not options["force"]:
                over = input("File already exists, do you want to overwrite it? (Y/n):")
                if over.lower() != "y":
                    exit(0)
            try:
                with Image.open(options["path"]) as im:
                    im.resize((120, 120)).save(dest_path, format="PNG")

                self.stdout.write("Promo logo moved and resized successfully")
            except IOError as ioe:
                self.stderr.write(ioe)
        else:
            self.stdout.write("input file does not exist.")
