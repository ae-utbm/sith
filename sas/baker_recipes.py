from django.conf import settings
from model_bakery import seq
from model_bakery.recipe import Recipe, foreign_key

from sas.models import Album, Picture

album_recipe = Recipe(
    Album,
    is_in_sas=True,
    is_folder=True,
    is_moderated=True,
    parent_id=settings.SITH_SAS_ROOT_DIR_ID,
    name=seq("Album "),
)

picture_recipe = Recipe(
    Picture,
    is_in_sas=True,
    is_folder=False,
    is_moderated=True,
    parent=foreign_key(album_recipe),
    name=seq("Picture "),
)
"""A SAS Picture fixture.

Warnings:
    If you don't `bulk_create` this, you need
    to explicitly set the parent album, or it won't work
"""
