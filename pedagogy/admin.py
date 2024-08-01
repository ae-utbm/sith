#
# Copyright 2019
# - Sli <antoine@bartuccio.fr>
#
# Ce fichier fait partie du site de l'Association des Étudiants de l'UTBM,
# http://ae.utbm.fr.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License a published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Sofware Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.
#
#
from django.contrib import admin
from haystack.admin import SearchModelAdmin

from pedagogy.models import UV, UVComment, UVCommentReport


@admin.register(UV)
class UVAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "credit_type", "credits", "department")
    search_fields = ("code", "title", "department")
    autocomplete_fields = ("author",)


@admin.register(UVComment)
class UVCommentAdmin(admin.ModelAdmin):
    list_display = ("author", "uv", "grade_global", "publish_date")
    search_fields = (
        "author__username",
        "author__first_name",
        "author__last_name",
        "uv__code",
    )
    autocomplete_fields = ("author",)


@admin.register(UVCommentReport)
class UVCommentReportAdmin(SearchModelAdmin):
    list_display = ("reporter", "uv")
    search_fields = (
        "reporter__username",
        "reporter__first_name",
        "reporter__last_name",
        "comment__uv__code",
    )
    autocomplete_fields = ("reporter",)
