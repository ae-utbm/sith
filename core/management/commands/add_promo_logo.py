import pathlib

from django.core.management.base import BaseCommand
from PIL import Image

from sith.settings import BASE_DIR


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("number", type=int)
        parser.add_argument("path", type=pathlib.Path)
        parser.add_argument("-f", "--force", action="store_true")

    def handle(self, number: int, path: pathlib.Path, force: int, *args, **options):
        if path.exists():
            dest_path = pathlib.Path(
                BASE_DIR / "core" / "static" / "core" / "img" / f"promo_{number}.png"
            )
            if dest_path.exists() and not force:
                over = input("File already exists, do you want to overwrite it? (y/N):")
                if over.lower() != "y":
                    return
            try:
                with Image.open(options["path"]) as im:
                    im.resize((120, 120)).save(dest_path, format="PNG")

                self.stdout.write(
                    f"Promo logo moved and resized successfully at {dest_path}"
                )
            except IOError as ioe:
                self.stderr.write(ioe)
        else:
            self.stdout.write("input file does not exist.")
