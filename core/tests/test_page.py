from datetime import timedelta

import freezegun
import pytest
from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.auth.models import Permission
from django.test import Client
from django.urls import reverse
from django.utils.timezone import now
from model_bakery import baker
from pytest_django.asserts import assertHTMLEqual, assertRedirects

from club.models import Club
from core.baker_recipes import board_user, subscriber_user
from core.markdown import markdown
from core.models import AnonymousUser, Page, PageRev, User


@pytest.mark.django_db
class TestEditPage:
    def test_edit_page(self, client: Client):
        user = board_user.make()
        page = baker.prepare(Page)
        page.save(force_lock=True)
        page.view_groups.add(user.groups.first())
        page.edit_groups.add(user.groups.first())
        client.force_login(user)

        url = reverse("core:page_edit", kwargs={"page_name": page._full_name})
        res = client.get(url)
        assert res.status_code == 200

        res = client.post(url, data={"content": "Hello World"})
        assertRedirects(
            res, reverse("core:page", kwargs={"page_name": page._full_name})
        )
        revision = page.revisions.last()
        assert revision.content == "Hello World"

    def test_pagerev_reused(self, client):
        """Test that the previous revision is edited, if same author and small time diff"""
        user = baker.make(User, is_superuser=True)
        page = baker.prepare(Page)
        page.save(force_lock=True)
        first_rev = baker.make(PageRev, author=user, page=page, date=now())
        client.force_login(user)
        url = reverse("core:page_edit", kwargs={"page_name": page._full_name})
        client.post(url, data={"content": "Hello World"})
        assert page.revisions.count() == 1
        assert page.revisions.last() == first_rev
        first_rev.refresh_from_db()
        assert first_rev.author == user
        assert first_rev.content == "Hello World"

    def test_pagerev_not_reused(self, client):
        """Test that a new revision is created if too much time
        passed since the last one.
        """
        user = baker.make(User, is_superuser=True)
        page = baker.prepare(Page)
        page.save(force_lock=True)
        first_rev = baker.make(PageRev, author=user, page=page, date=now())
        client.force_login(user)
        url = reverse("core:page_edit", kwargs={"page_name": page._full_name})
        with freezegun.freeze_time(now() + timedelta(minutes=30)):
            client.post(url, data={"content": "Hello World"})
        assert page.revisions.count() == 2
        assert page.revisions.last() != first_rev


@pytest.mark.django_db
def test_page_revision(client: Client):
    page = baker.prepare(Page)
    page.save(force_lock=True)
    page.view_groups.add(settings.SITH_GROUP_SUBSCRIBERS_ID)
    revisions = baker.make(
        PageRev, page=page, _quantity=3, content=iter(["foo", "bar", "baz"])
    )
    client.force_login(subscriber_user.make())
    url = reverse(
        "core:page_rev",
        kwargs={"page_name": page._full_name, "rev": revisions[1].id},
    )
    res = client.get(url)
    assert res.status_code == 200
    soup = BeautifulSoup(res.text, "lxml")
    detail_html = soup.find(class_="markdown")
    assertHTMLEqual(detail_html.decode_contents(), markdown(revisions[1].content))


@pytest.mark.django_db
def test_page_club_redirection(client: Client):
    club = baker.make(Club)
    url = reverse("core:page", kwargs={"page_name": club.page._full_name})
    res = client.get(url)
    redirection_url = reverse("club:club_view", kwargs={"club_id": club.id})
    assertRedirects(res, redirection_url)


@pytest.mark.django_db
def test_page_revision_club_redirection(client: Client):
    client.force_login(subscriber_user.make())
    club = baker.make(Club)
    revisions = baker.make(
        PageRev, page=club.page, _quantity=3, content=iter(["foo", "bar", "baz"])
    )
    url = reverse(
        "core:page_rev",
        kwargs={"page_name": club.page._full_name, "rev": revisions[1].id},
    )
    res = client.get(url)
    redirection_url = reverse(
        "club:club_view_rev", kwargs={"club_id": club.id, "rev_id": revisions[1].id}
    )
    assertRedirects(res, redirection_url)


@pytest.mark.django_db
def test_viewable_by():
    # remove existing pages to prevent side effect
    Page.objects.all().delete()
    view_groups = [
        [settings.SITH_GROUP_PUBLIC_ID],
        [settings.SITH_GROUP_PUBLIC_ID, settings.SITH_GROUP_SUBSCRIBERS_ID],
        [settings.SITH_GROUP_SUBSCRIBERS_ID],
        [settings.SITH_GROUP_SUBSCRIBERS_ID, settings.SITH_GROUP_OLD_SUBSCRIBERS_ID],
        [],
    ]
    pages = baker.make(Page, _quantity=len(view_groups), _bulk_create=True)
    for page, groups in zip(pages, view_groups, strict=True):
        page.view_groups.set(groups)

    viewable = Page.objects.viewable_by(AnonymousUser()).values_list("id", flat=True)
    assert set(viewable) == {pages[0].id, pages[1].id}

    subscriber = subscriber_user.make()
    viewable = Page.objects.viewable_by(subscriber).values_list("id", flat=True)
    assert set(viewable) == {p.id for p in pages[0:4]}

    root_user = baker.make(
        User, user_permissions=[Permission.objects.get(codename="view_page")]
    )
    viewable = Page.objects.viewable_by(root_user).values_list("id", flat=True)
    assert set(viewable) == {p.id for p in pages}


@pytest.mark.django_db
def test_page_list_view(client: Client):
    baker.make(Page, _quantity=10, _bulk_create=True)
    client.force_login(subscriber_user.make())
    res = client.get(reverse("core:page_list"))
    assert res.status_code == 200
