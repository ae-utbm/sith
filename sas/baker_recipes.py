from model_bakery import seq
from model_bakery.recipe import Recipe

from sas.models import Picture

picture_recipe = Recipe(
    Picture,
    is_in_sas=True,
    is_folder=False,
    is_moderated=True,
    name=seq("Picture "),
)
"""A SAS Picture fixture.

Warnings:
    If you don't `bulk_create` this, you need
    to explicitly set the parent album, or it won't work
"""
