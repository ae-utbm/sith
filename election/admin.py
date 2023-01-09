from ajax_select import make_ajax_form
from django.contrib import admin

from election.models import Election, Role, ElectionList, Candidature


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "is_candidature_active",
        "is_vote_active",
        "is_vote_finished",
        "archived",
    )
    form = make_ajax_form(Election, {"voters": "users"})


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("election", "title", "max_choice")
    search_fields = ("election__title", "title")


@admin.register(ElectionList)
class ElectionListAdmin(admin.ModelAdmin):
    list_display = ("election", "title")
    search_fields = ("election__title", "title")


@admin.register(Candidature)
class CandidatureAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "election_list")
    form = make_ajax_form(Candidature, {"user": "users"})


# Votes must stay fully anonymous, so no ModelAdmin for Vote model
