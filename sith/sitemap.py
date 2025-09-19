from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.db.models import OuterRef, Subquery
from django.urls import reverse

from club.models import Club
from core.models import Page, PageRev


class SithSitemap(Sitemap):
    def items(self):
        return [
            "core:index",
            "eboutic:main",
            "sas:main",
            "forum:main",
            "club:club_list",
            "election:list",
        ]

    def location(self, item):
        return reverse(item)


class PagesSitemap(Sitemap):
    def items(self):
        return (
            Page.objects.filter(view_groups=settings.SITH_GROUP_PUBLIC_ID)
            .exclude(revisions=None, _full_name__startswith="club")
            .annotate(
                lastmod=Subquery(
                    PageRev.objects.filter(page=OuterRef("pk"))
                    .values("date")
                    .order_by("-date")[:1]
                )
            )
            .all()
        )

    def lastmod(self, item: Page):
        return item.lastmod


class ClubSitemap(Sitemap):
    def items(self):
        return Club.objects.filter(is_active=True)
