from typing import TYPE_CHECKING, Callable

import pytest
from aemark import markdown
from bs4 import BeautifulSoup
from django.contrib.auth.models import Permission
from django.urls import reverse
from model_bakery import baker
from pytest_django.asserts import assertHTMLEqual, assertRedirects

from club.models import Club, ClubRole, Membership
from core.baker_recipes import subscriber_user
from core.models import PageRev, User

if TYPE_CHECKING:
    from django.test import Client


@pytest.mark.django_db
@pytest.mark.parametrize("user_factory", [lambda: None, subscriber_user.make])
def test_page_display_on_club_main_page(
    client: Client, user_factory: Callable[[], User | None]
):
    """Test the club Page is properly displayed on the club main view"""
    club = baker.make(Club)
    # create another previous revision, to test that we display the most recent one
    baker.make(PageRev, page=club.page, revision=1)
    content = "# foo\nLorem ipsum dolor sit amet"
    baker.make(PageRev, page=club.page, revision=2, content=content)

    if user := user_factory():
        client.force_login(user)
    res = client.get(reverse("club:club_view", kwargs={"club_id": club.id}))
    assert res.status_code == 200
    soup = BeautifulSoup(res.text, "lxml")
    detail_html = soup.find(id="club-page").find(class_="markdown")
    assertHTMLEqual(detail_html.decode_contents(), markdown(content))


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("user_factory", "can_view_tabs", "can_view_edit_button"),
    [
        (lambda _: None, False, False),
        (lambda _: baker.make(User), False, False),
        (lambda _: subscriber_user.make(), True, False),
        (
            # admin user
            lambda _: subscriber_user.make(
                user_permissions=[Permission.objects.get(codename="change_club")]
            ),
            True,
            True,
        ),
        (
            # club board member
            lambda club: (
                baker.make(
                    Membership,
                    club=club,
                    role=baker.make(ClubRole, is_board=True),
                    user=subscriber_user.make(),
                ).user
            ),
            True,
            True,
        ),
    ],
    ids=["anonymous", "public", "subscriber", "admin", "club board"],
)
@pytest.mark.django_db
def test_club_main_page_displayed_elements(
    client: Client, user_factory, can_view_tabs, can_view_edit_button
):
    """Test that the appropriate elements are displayed depending on user status."""
    club = baker.make(Club)
    if user := user_factory(club):
        client.force_login(user)
    res = client.get(reverse("club:club_view", kwargs={"club_id": club.id}))

    assert res.status_code == 200
    soup = BeautifulSoup(res.text, "lxml")
    tabs = soup.find(class_="tool_bar")
    assert tabs is not None if can_view_tabs else tabs is None
    edit_btn = soup.find(
        "a",
        href=reverse("core:page_edit", kwargs={"page_name": club.page.get_full_name()}),
    )
    assert edit_btn is not None if can_view_edit_button else edit_btn is None


@pytest.mark.django_db
def test_page_revision(client: Client):
    """Test that accessing a previous revision of the club page works."""
    club = baker.make(Club)
    revisions = baker.make(
        PageRev, page=club.page, _quantity=3, content=iter(["foo", "bar", "baz"])
    )
    client.force_login(baker.make(User))
    url = reverse(
        "club:club_view_rev", kwargs={"club_id": club.id, "rev_id": revisions[1].id}
    )
    res = client.get(url)
    assert res.status_code == 200
    soup = BeautifulSoup(res.text, "lxml")
    detail_html = soup.find(class_="markdown")
    assertHTMLEqual(detail_html.decode_contents(), markdown(revisions[1].content))


@pytest.mark.django_db
def test_edit_page(client: Client):
    club = baker.make(Club)
    user = subscriber_user.make()
    baker.make(
        Membership,
        user=user,
        club=club,
        role=baker.make(ClubRole, club=club, is_board=True),
    )
    client.force_login(user)
    url = reverse("club:club_edit_page", kwargs={"club_id": club.id})
    content = "# foo\nLorem ipsum dolor sit amet"

    res = client.get(url)
    assert res.status_code == 200
    res = client.post(url, data={"content": content})
    assertRedirects(res, reverse("club:club_view", kwargs={"club_id": club.id}))
    assert club.page.revisions.last().content == content
