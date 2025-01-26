from django.conf import settings
from model_bakery import seq
from model_bakery.recipe import Recipe, foreign_key

from sas.models import Album, Picture

album_recipe = Recipe(Album, is_moderated=True, name=seq("Album "))

picture_recipe = Recipe(
    Picture, is_moderated=True, album=foreign_key(album_recipe), name=seq("Picture ")
)
"""A SAS Picture fixture.

Warnings:
    If you don't `bulk_create` this, you need
    to explicitly set the parent album, or it won't work
"""
