from django.contrib import admin

from election.models import Candidature, Election, ElectionList, Role


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "is_candidature_active",
        "is_vote_active",
        "is_vote_finished",
        "archived",
    )
    autocomplete_fields = ("voters",)


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
    autocomplete_fields = ("user",)


# Votes must stay fully anonymous, so no ModelAdmin for Vote model
