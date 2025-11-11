import pytest
from bs4 import BeautifulSoup
from django.test import Client
from django.urls import reverse
from model_bakery import baker
from pytest_django.asserts import assertHTMLEqual, assertRedirects

from club.models import Club, Membership
from core.baker_recipes import subscriber_user
from core.markdown import markdown
from core.models import PageRev, User


@pytest.mark.django_db
def test_page_display_on_club_main_page(client: Client):
    """Test the club Page is properly displayed on the club main view"""
    club = baker.make(Club)
    content = "# foo\nLorem ipsum dolor sit amet"
    baker.make(PageRev, page=club.page, revision=1, content=content)
    res = client.get(reverse("club:club_view", kwargs={"club_id": club.id}))

    assert res.status_code == 200
    soup = BeautifulSoup(res.text, "lxml")
    detail_html = soup.find(id="club_detail").find(class_="markdown")
    assertHTMLEqual(detail_html.decode_contents(), markdown(content))


@pytest.mark.django_db
def test_club_main_page_without_content(client: Client):
    """Test the club view works, even if the club page is empty"""
    club = baker.make(Club)
    club.page.revisions.all().delete()
    res = client.get(reverse("club:club_view", kwargs={"club_id": club.id}))

    assert res.status_code == 200
    soup = BeautifulSoup(res.text, "lxml")
    detail_html = soup.find(id="club_detail")
    assert detail_html.find_all("markdown") == []


@pytest.mark.django_db
def test_page_revision(client: Client):
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
    baker.make(Membership, user=user, club=club, role=3)
    client.force_login(user)
    url = reverse("club:club_edit_page", kwargs={"club_id": club.id})
    content = "# foo\nLorem ipsum dolor sit amet"

    res = client.get(url)
    assert res.status_code == 200
    res = client.post(url, data={"content": content})
    assertRedirects(res, reverse("club:club_view", kwargs={"club_id": club.id}))
    assert club.page.revisions.last().content == content
