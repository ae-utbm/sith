from django.core.files.uploadedfile import SimpleUploadedFile
from model_bakery import seq
from model_bakery.recipe import Recipe

from core.utils import RED_PIXEL_PNG
from sas.models import Album, Picture

album_recipe = Recipe(
    Album,
    name=seq("Album "),
    thumbnail=SimpleUploadedFile(
        name="thumb.webp", content=b"", content_type="image/webp"
    ),
)


picture_recipe = Recipe(
    Picture,
    is_moderated=True,
    name=seq("Picture "),
    original=SimpleUploadedFile(
        # compressed and thumbnail are generated on save (except if bulk creating).
        # For this step no to fail, original must be a valid image.
        name="img.png",
        content=RED_PIXEL_PNG,
        content_type="image/png",
    ),
    compressed=SimpleUploadedFile(
        name="img.webp", content=b"", content_type="image/webp"
    ),
    thumbnail=SimpleUploadedFile(
        name="img.webp", content=b"", content_type="image/webp"
    ),
)
"""A SAS Picture fixture."""
