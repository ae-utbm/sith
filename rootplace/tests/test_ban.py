from datetime import datetime, timedelta
from io import BytesIO

import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from django.urls import reverse
from django.utils.timezone import localdate, localtime
from model_bakery import baker
from pypdf import PdfReader
from pytest_django.asserts import assertRedirects

from core.models import BanGroup, User, UserBan


@pytest.fixture
def operator(db) -> User:
    return baker.make(
        User,
        user_permissions=Permission.objects.filter(
            codename__in=["view_userban", "add_userban", "delete_userban"]
        ),
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "expires_at",
    [None, localtime().replace(second=0, microsecond=0) + timedelta(days=7)],
)
def test_ban_user(client: Client, operator: User, expires_at: datetime):
    client.force_login(operator)
    user = baker.make(User)
    ban_group = BanGroup.objects.first()
    data = {
        "user": user.id,
        "ban_group": ban_group.id,
        "reason": "Being naughty",
    }
    if expires_at is not None:
        data["expires_at"] = expires_at.strftime("%Y-%m-%d %H:%M")
    response = client.post(reverse("rootplace:ban_create"), data)
    assertRedirects(response, expected_url=reverse("rootplace:ban_list"))
    bans = list(user.bans.all())
    assert len(bans) == 1
    assert bans[0].expires_at == expires_at
    assert bans[0].reason == "Being naughty"
    assert bans[0].ban_group == ban_group


@pytest.mark.django_db
def test_remove_ban(client: Client, operator: User):
    client.force_login(operator)
    user = baker.make(User)
    ban = baker.make(UserBan, user=user)
    assert user.bans.exists()
    response = client.post(reverse("rootplace:ban_remove", kwargs={"ban_id": ban.id}))
    assertRedirects(response, expected_url=reverse("rootplace:ban_list"))
    assert not user.bans.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "mode,language,ban_group,expected_names,unexpected_names,expected_reason",
    [
        ("image", "fr", None, ["John Doe", "Jane Smith"], [], None),
        ("desc", "fr", None, ["Alice Wonder"], [], "Detailed test reason"),
        ("desc", "en", None, ["Test User"], [], "Test"),
        ("desc", "fr", "filter", ["Filtered User"], ["Other User"], "First group"),
        ("image", "fr", None, [], [], None),  # no banned users
    ],
)
def test_ban_report_pdf_parametrized(
    client: Client,
    operator: User,
    mode,
    language,
    ban_group,
    expected_names,
    unexpected_names,
    expected_reason,
):
    """Test PDF generation for various modes, languages, and ban_group filters."""
    client.force_login(operator)
    today = localdate()
    now = localtime()
    # Préparation des données selon le cas
    if mode == "image" and expected_names == ["John Doe", "Jane Smith"]:
        ban_group_obj = BanGroup.objects.first()
        user1 = baker.make(User, first_name="John", last_name="Doe")
        user2 = baker.make(User, first_name="Jane", last_name="Smith")
        baker.make(
            UserBan,
            user=user1,
            ban_group=ban_group_obj,
            reason="Test reason 1",
            created_at=now - timedelta(days=1),
            expires_at=None,
        )
        baker.make(
            UserBan,
            user=user2,
            ban_group=ban_group_obj,
            reason="Test reason 2",
            created_at=now - timedelta(days=1),
            expires_at=now + timedelta(days=30),
        )
    elif mode == "desc" and expected_names == ["Alice Wonder"]:
        ban_group_obj = BanGroup.objects.first()
        user = baker.make(User, first_name="Alice", last_name="Wonder")
        baker.make(
            UserBan,
            user=user,
            ban_group=ban_group_obj,
            reason="Detailed test reason",
            created_at=now - timedelta(days=5),
            expires_at=now + timedelta(days=10),
        )
    elif mode == "desc" and expected_names == ["Test User"]:
        ban_group_obj = BanGroup.objects.first()
        user = baker.make(User, first_name="Test", last_name="User")
        baker.make(
            UserBan,
            user=user,
            ban_group=ban_group_obj,
            reason="Test",
            created_at=now - timedelta(days=1),
        )
    elif mode == "desc" and ban_group == "filter":
        ban_groups = list(BanGroup.objects.all()[:2])
        if len(ban_groups) < 2:
            pytest.skip("Need at least 2 ban groups for this test")
        user1 = baker.make(User, first_name="Filtered", last_name="User")
        user2 = baker.make(User, first_name="Other", last_name="User")
        baker.make(
            UserBan,
            user=user1,
            ban_group=ban_groups[0],
            reason="First group",
            created_at=now - timedelta(days=1),
        )
        baker.make(
            UserBan,
            user=user2,
            ban_group=ban_groups[1],
            reason="Second group",
            created_at=now - timedelta(days=1),
        )
    # pas de bans pour le cas "no banned users"
    # Construction des données du POST
    post_data = {
        "date": today.strftime("%Y-%m-%d"),
        "mode": mode,
        "language": language,
    }
    if ban_group == "filter":
        post_data["ban_group"] = ban_groups[0].id
    response = client.post(reverse("rootplace:ban_report"), post_data)
    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    pdf_content = BytesIO(response.content)
    pdf_reader = PdfReader(pdf_content)
    assert len(pdf_reader.pages) > 0
    page_text = pdf_reader.pages[0].extract_text()
    for name in expected_names:
        assert name in page_text
    for name in unexpected_names:
        assert name not in page_text
    if expected_reason:
        assert expected_reason in page_text
