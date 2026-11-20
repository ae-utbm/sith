from modeltranslation.translator import TranslationOptions, register

from club.models import ClubRole


@register(ClubRole)
class ClubRoleTranslationOptions(TranslationOptions):
    fields = ("name",)
