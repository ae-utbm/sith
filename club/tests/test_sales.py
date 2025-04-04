import pytest
from django.test import Client
from django.urls import reverse
from model_bakery import baker

from club.models import Club
from core.models import User


@pytest.mark.django_db
def test_sales_page_doesnt_crash(client: Client):
    club = baker.make(Club)
    admin = baker.make(User, is_superuser=True)
    client.force_login(admin)
    response = client.get(reverse("club:club_sellings", kwargs={"club_id": club.id}))
    assert response.status_code == 200
