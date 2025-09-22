import pytest
from django.test import Client
from django.urls import reverse
from model_bakery import baker
from pytest_django.asserts import assertRedirects

from core.baker_recipes import board_user
from core.models import Page


@pytest.mark.django_db
def test_edit_page(client: Client):
    user = board_user.make()
    page = baker.prepare(Page)
    page.save(force_lock=True)
    page.view_groups.add(user.groups.first())
    client.force_login(user)

    url = reverse("core:page_edit", kwargs={"page_name": page._full_name})
    res = client.get(url)
    assert res.status_code == 200

    res = client.post(url, data={"content": "Hello World"})
    assertRedirects(res, reverse("core:page", kwargs={"page_name": page._full_name}))
    revision = page.revisions.last()
    assert revision.content == "Hello World"
