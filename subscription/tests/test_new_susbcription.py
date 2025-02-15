"""Tests focused on testing subscription creation"""

from datetime import timedelta
from typing import Callable

import pytest
from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import Permission
from django.test import Client
from django.urls import reverse
from django.utils.timezone import localdate
from model_bakery import baker
from pytest_django.asserts import assertRedirects
from pytest_django.fixtures import SettingsWrapper

from core.baker_recipes import board_user, old_subscriber_user, subscriber_user
from core.models import User
from subscription.forms import SubscriptionExistingUserForm, SubscriptionNewUserForm


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_factory",
    [old_subscriber_user.make, lambda: baker.make(User)],
)
def test_form_existing_user_valid(
    user_factory: Callable[[], User], settings: SettingsWrapper
):
    """Test `SubscriptionExistingUserForm`"""
    user = user_factory()
    data = {
        "member": user,
        "subscription_type": "deux-semestres",
        "location": settings.SITH_SUBSCRIPTION_LOCATIONS[0][0],
        "payment_method": settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0][0],
    }
    form = SubscriptionExistingUserForm(data)

    assert form.is_valid()
    form.save()
    user.refresh_from_db()
    assert user.is_subscribed


@pytest.mark.django_db
def test_form_existing_user_invalid(settings: SettingsWrapper):
    """Test `SubscriptionExistingUserForm`, with users that shouldn't subscribe."""
    user = subscriber_user.make()
    # make sure the current subscription will end in a long time
    last_sub = user.subscriptions.order_by("subscription_end").last()
    last_sub.subscription_end = localdate() + timedelta(weeks=50)
    last_sub.save()
    data = {
        "member": user,
        "subscription_type": "deux-semestres",
        "location": settings.SITH_SUBSCRIPTION_LOCATIONS[0][0],
        "payment_method": settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0][0],
    }
    form = SubscriptionExistingUserForm(data)

    assert not form.is_valid()
    with pytest.raises(ValueError):
        form.save()


@pytest.mark.django_db
def test_form_new_user(settings: SettingsWrapper):
    data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "jdoe@utbm.fr",
        "date_of_birth": localdate() - relativedelta(years=18),
        "subscription_type": "deux-semestres",
        "location": settings.SITH_SUBSCRIPTION_LOCATIONS[0][0],
        "payment_method": settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0][0],
    }
    form = SubscriptionNewUserForm(data)
    assert form.is_valid()
    form.save()
    user = User.objects.get(email="jdoe@utbm.fr")
    assert user.username == "jdoe"
    assert user.is_subscribed

    # if trying to instantiate a new form with the same email,
    # it should fail
    form = SubscriptionNewUserForm(data)
    assert not form.is_valid()
    with pytest.raises(ValueError):
        form.save()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("user_factory", "status_code"),
    [
        (lambda: baker.make(User, is_superuser=True), 200),
        (board_user.make, 200),
        (subscriber_user.make, 403),
    ],
)
def test_page_access(
    client: Client, user_factory: Callable[[], User], status_code: int
):
    """Check that only authorized users may access this page."""
    client.force_login(user_factory())
    res = client.get(reverse("subscription:subscription"))
    assert res.status_code == status_code


@pytest.mark.django_db
def test_submit_form_existing_user(client: Client, settings: SettingsWrapper):
    client.force_login(
        baker.make(
            User,
            user_permissions=Permission.objects.filter(codename="add_subscription"),
        )
    )
    user = old_subscriber_user.make()
    response = client.post(
        reverse("subscription:fragment-existing-user"),
        {
            "member": user.id,
            "subscription_type": "deux-semestres",
            "location": settings.SITH_SUBSCRIPTION_LOCATIONS[0][0],
            "payment_method": settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0][0],
        },
    )
    user.refresh_from_db()
    assert user.is_subscribed
    current_subscription = user.subscriptions.order_by("-subscription_start").first()
    assertRedirects(
        response,
        reverse(
            "subscription:creation-success",
            kwargs={"subscription_id": current_subscription.id},
        ),
    )


@pytest.mark.django_db
def test_submit_form_new_user(client: Client, settings: SettingsWrapper):
    client.force_login(
        baker.make(
            User,
            user_permissions=Permission.objects.filter(codename="add_subscription"),
        )
    )
    response = client.post(
        reverse("subscription:fragment-new-user"),
        {
            "first_name": "John",
            "last_name": "Doe",
            "email": "jdoe@utbm.fr",
            "date_of_birth": localdate() - relativedelta(years=18),
            "subscription_type": "deux-semestres",
            "location": settings.SITH_SUBSCRIPTION_LOCATIONS[0][0],
            "payment_method": settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0][0],
        },
    )
    user = User.objects.get(email="jdoe@utbm.fr")
    assert user.is_subscribed
    current_subscription = user.subscriptions.order_by("-subscription_start").first()
    assertRedirects(
        response,
        reverse(
            "subscription:creation-success",
            kwargs={"subscription_id": current_subscription.id},
        ),
    )
