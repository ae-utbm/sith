import pytest
from bs4 import BeautifulSoup
from django.test import Client
from django.urls import reverse
from model_bakery import baker
from pytest_django.asserts import assertHTMLEqual

from club.models import Club
from core.markdown import markdown
from core.models import PageRev, User


@pytest.mark.django_db
def test_page_display_on_club_main_page(client: Client):
    """Test the club Page is properly displayed on the club main view"""
    club = baker.make(Club)
    content = "# foo\nLorem ipsum dolor sit amet"
    baker.make(PageRev, page=club.page, revision=1, content=content)
    client.force_login(baker.make(User))
    res = client.get(reverse("club:club_view", kwargs={"club_id": club.id}))

    assert res.status_code == 200
    soup = BeautifulSoup(res.content.decode(), "lxml")
    detail_html = soup.find(id="club_detail").find(class_="markdown")
    assertHTMLEqual(detail_html.decode_contents(), markdown(content))


@pytest.mark.django_db
def test_club_main_page_without_content(client: Client):
    """Test the club view works, even if the club page is empty"""
    club = baker.make(Club)
    club.page.revisions.all().delete()
    client.force_login(baker.make(User))
    res = client.get(reverse("club:club_view", kwargs={"club_id": club.id}))

    assert res.status_code == 200
    soup = BeautifulSoup(res.content.decode(), "lxml")
    detail_html = soup.find(id="club_detail")
    assert detail_html.find_all("markdown") == []
