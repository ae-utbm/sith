import pathlib

from django.apps import apps
from django.core.management.base import BaseCommand
from PIL import Image, UnidentifiedImageError


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("number", type=int)
        parser.add_argument("path", type=pathlib.Path)
        parser.add_argument("-f", "--force", action="store_true")

    def handle(self, number: int, path: pathlib.Path, force: int, *args, **options):
        if not path.exists() or path.is_dir():
            self.stderr.write(f"{path} is not a file or does not exist")
            return

        dest_path = (
            pathlib.Path(apps.get_app_config("core").path)
            / "static"
            / "core"
            / "img"
            / f"promo_{number}.png"
        )

        if dest_path.exists() and not force:
            over = input("File already exists, do you want to overwrite it? (y/N):")
            if over.lower() != "y":
                self.stdout.write("exiting")
                return
        try:
            im = Image.open(path)
            im.resize((120, 120), resample=Image.Resampling.LANCZOS).save(
                dest_path, format="PNG"
            )
            self.stdout.write(
                f"Promo logo moved and resized successfully at {dest_path}"
            )
        except UnidentifiedImageError:
            self.stderr.write("image cannot be opened and identified.")
