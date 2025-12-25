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
class TestBanReportPDFView:
    """Tests for the BanReportPDFView."""

    def test_access_without_permission(self, client: Client):
        """Test that users without permission cannot access the ban report view."""
        user = baker.make(User)
        client.force_login(user)
        response = client.get(reverse("rootplace:ban_report"))
        assert response.status_code == 403

    def test_access_with_permission(self, client: Client, operator: User):
        """Test that users with permission can access the ban report form."""
        client.force_login(operator)
        response = client.get(reverse("rootplace:ban_report"))
        assert response.status_code == 200

    def test_generate_pdf_image_mode(self, client: Client, operator: User):
        """Test PDF generation in image mode (grid of profile pictures)."""
        client.force_login(operator)

        # Create banned users
        ban_group = BanGroup.objects.first()
        today = localdate()
        now = localtime()
        user1 = baker.make(User, first_name="John", last_name="Doe")
        user2 = baker.make(User, first_name="Jane", last_name="Smith")

        baker.make(
            UserBan,
            user=user1,
            ban_group=ban_group,
            reason="Test reason 1",
            created_at=now - timedelta(days=1),
            expires_at=None,
        )
        baker.make(
            UserBan,
            user=user2,
            ban_group=ban_group,
            reason="Test reason 2",
            created_at=now - timedelta(days=1),
            expires_at=now + timedelta(days=30),
        )

        # Generate PDF
        response = client.post(
            reverse("rootplace:ban_report"),
            {
                "date": today.strftime("%Y-%m-%d"),
                "mode": "image",
                "language": "fr",
            },
        )

        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"
        assert "attachment" in response["Content-Disposition"]
        assert f"banned_users_{today}.pdf" in response["Content-Disposition"]

        # Verify PDF content
        pdf_content = BytesIO(response.content)
        pdf_reader = PdfReader(pdf_content)
        assert len(pdf_reader.pages) > 0

        # Check that text contains user names
        page_text = pdf_reader.pages[0].extract_text()
        assert "John Doe" in page_text
        assert "Jane Smith" in page_text

    def test_generate_pdf_desc_mode(self, client: Client, operator: User):
        """Test PDF generation in desc mode (detailed list with reasons)."""
        client.force_login(operator)

        # Create banned user
        ban_group = BanGroup.objects.first()
        today = localdate()
        now = localtime()
        user = baker.make(User, first_name="Alice", last_name="Wonder")

        baker.make(
            UserBan,
            user=user,
            ban_group=ban_group,
            reason="Detailed test reason",
            created_at=now - timedelta(days=5),
            expires_at=now + timedelta(days=10),
        )

        # Generate PDF
        response = client.post(
            reverse("rootplace:ban_report"),
            {
                "date": today.strftime("%Y-%m-%d"),
                "mode": "desc",
                "language": "fr",
            },
        )

        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"

        # Verify PDF content
        pdf_content = BytesIO(response.content)
        pdf_reader = PdfReader(pdf_content)
        assert len(pdf_reader.pages) > 0

        # Check that text contains user info and reason
        page_text = pdf_reader.pages[0].extract_text()
        assert "Alice Wonder" in page_text
        assert "Detailed test reason" in page_text

    def test_generate_pdf_with_ban_group_filter(self, client: Client, operator: User):
        """Test PDF generation with ban_group filter."""
        client.force_login(operator)

        # Get two different ban groups
        ban_groups = list(BanGroup.objects.all()[:2])
        if len(ban_groups) < 2:
            pytest.skip("Need at least 2 ban groups for this test")

        today = localdate()
        now = localtime()
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

        # Generate PDF filtered by first ban group
        response = client.post(
            reverse("rootplace:ban_report"),
            {
                "date": today.strftime("%Y-%m-%d"),
                "mode": "desc",
                "language": "fr",
                "ban_group": ban_groups[0].id,
            },
        )

        assert response.status_code == 200

        # Verify only the filtered user appears
        pdf_content = BytesIO(response.content)
        pdf_reader = PdfReader(pdf_content)
        page_text = pdf_reader.pages[0].extract_text()
        assert "Filtered User" in page_text
        assert "Other User" not in page_text

    def test_generate_pdf_english_language(self, client: Client, operator: User):
        """Test PDF generation with English language."""
        client.force_login(operator)

        ban_group = BanGroup.objects.first()
        today = localdate()
        now = localtime()
        user = baker.make(User, first_name="Test", last_name="User")

        baker.make(
            UserBan,
            user=user,
            ban_group=ban_group,
            reason="Test",
            created_at=now - timedelta(days=1),
        )

        # Generate PDF in English
        response = client.post(
            reverse("rootplace:ban_report"),
            {
                "date": today.strftime("%Y-%m-%d"),
                "mode": "desc",
                "language": "en",
            },
        )

        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"

        # The translations should be in English
        pdf_content = BytesIO(response.content)
        pdf_reader = PdfReader(pdf_content)
        page_text = pdf_reader.pages[0].extract_text()
        # Just verify the PDF was generated successfully
        # (actual text content depends on translations)
        assert len(page_text) > 0

    def test_generate_pdf_no_banned_users(self, client: Client, operator: User):
        """Test PDF generation when no users are banned on the selected date."""
        client.force_login(operator)

        today = localdate()

        # Generate PDF with no bans
        response = client.post(
            reverse("rootplace:ban_report"),
            {
                "date": today.strftime("%Y-%m-%d"),
                "mode": "image",
                "language": "fr",
            },
        )

        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"

        # PDF should still be valid even with no users
        pdf_content = BytesIO(response.content)
        pdf_reader = PdfReader(pdf_content)
        assert len(pdf_reader.pages) > 0
