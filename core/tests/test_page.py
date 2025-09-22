import pytest
from django.conf import settings
from django.contrib.auth.models import Permission
from django.test import Client
from django.urls import reverse
from model_bakery import baker
from pytest_django.asserts import assertRedirects

from core.baker_recipes import board_user, subscriber_user
from core.models import AnonymousUser, Page, User
from sith.settings import SITH_GROUP_OLD_SUBSCRIBERS_ID, SITH_GROUP_SUBSCRIBERS_ID


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


@pytest.mark.django_db
def test_viewable_by():
    # remove existing pages to prevent side effect
    Page.objects.all().delete()
    view_groups = [
        [settings.SITH_GROUP_PUBLIC_ID],
        [settings.SITH_GROUP_PUBLIC_ID, SITH_GROUP_SUBSCRIBERS_ID],
        [SITH_GROUP_SUBSCRIBERS_ID],
        [SITH_GROUP_SUBSCRIBERS_ID, SITH_GROUP_OLD_SUBSCRIBERS_ID],
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
