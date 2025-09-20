"""Tests focused on testing subscription creation"""

from datetime import date, timedelta
from typing import Callable

import pytest
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth.models import Permission
from django.test import Client
from django.urls import reverse
from django.utils.timezone import localdate
from model_bakery import baker
from pytest_django.asserts import assertRedirects
from pytest_django.fixtures import SettingsWrapper

from core.baker_recipes import board_user, old_subscriber_user, subscriber_user
from core.models import Group, User
from counter.models import Customer
from subscription.forms import SubscriptionExistingUserForm, SubscriptionNewUserForm
from subscription.models import Subscription


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
    user.date_of_birth = date(year=1967, month=3, day=14)
    user.save()
    data = {
        "member": user,
        "birthdate": user.date_of_birth,
        "subscription_type": "deux-semestres",
        "location": settings.SITH_SUBSCRIPTION_LOCATIONS[0][0],
        "payment_method": settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[1][0],
    }
    form = SubscriptionExistingUserForm(data)
    assert form.is_valid()
    form.save()
    user.refresh_from_db()
    assert user.is_subscribed


@pytest.mark.django_db
def test_form_existing_user_with_birthdate(settings: SettingsWrapper):
    """Test `SubscriptionExistingUserForm`"""
    user = baker.make(User, date_of_birth=None)
    data = {
        "member": user,
        "subscription_type": "deux-semestres",
        "location": settings.SITH_SUBSCRIPTION_LOCATIONS[0][0],
        "payment_method": settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[1][0],
    }
    form = SubscriptionExistingUserForm(data)
    assert not form.is_valid()

    data |= {"birthdate": date(year=1967, month=3, day=14)}
    form = SubscriptionExistingUserForm(data)
    assert form.is_valid()
    form.save()
    user.refresh_from_db()
    assert user.is_subscribed
    assert user.date_of_birth == date(year=1967, month=3, day=14)


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
        "payment_method": settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[1][0],
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
        "payment_method": settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[1][0],
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
    "subscription_type",
    ["un-semestre", "deux-semestres", "cursus-tronc-commun", "cursus-branche"],
)
def test_form_set_new_user_as_student(settings: SettingsWrapper, subscription_type):
    """Test that new users have the student role by default."""
    data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "jdoe@utbm.fr",
        "date_of_birth": localdate() - relativedelta(years=18),
        "subscription_type": subscription_type,
        "location": settings.SITH_SUBSCRIPTION_LOCATIONS[0][0],
        "payment_method": settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[1][0],
    }
    form = SubscriptionNewUserForm(data)
    assert form.is_valid()
    form.clean()
    assert form.instance.member.role == "STUDENT"


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
def test_page_access_with_get_data(client: Client):
    user = old_subscriber_user.make()
    client.force_login(baker.make(User, is_superuser=True))
    res = client.get(reverse("subscription:subscription", query={"member": user.id}))
    assert res.status_code == 200


@pytest.mark.django_db
def test_submit_form_existing_user(client: Client, settings: SettingsWrapper):
    client.force_login(
        baker.make(
            User,
            user_permissions=Permission.objects.filter(codename="add_subscription"),
        )
    )
    user = old_subscriber_user.make(date_of_birth=date(year=1967, month=3, day=14))
    response = client.post(
        reverse("subscription:fragment-existing-user"),
        {
            "member": user.id,
            "birthdate": user.date_of_birth,
            "subscription_type": "deux-semestres",
            "location": settings.SITH_SUBSCRIPTION_LOCATIONS[0][0],
            "payment_method": settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[1][0],
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
            "payment_method": settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[1][0],
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


@pytest.mark.django_db
def test_subscription_for_user_that_had_a_sith_account():
    """Test that a newly subscribed user is added to the old subscribers group,
    even if there already was a sith account (e.g. created during an eboutic purchase).
    """
    user = baker.make(User)
    Customer.get_or_create(user)
    group = Group.objects.get(id=settings.SITH_GROUP_OLD_SUBSCRIBERS_ID)
    assert not user.groups.contains(group)
    subscription = baker.prepare(Subscription, member=user)
    subscription.save()
    assert user.groups.contains(group)
