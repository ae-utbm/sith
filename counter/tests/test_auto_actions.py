import json
from datetime import timedelta

import pytest
from django.conf import settings
from django.test import Client
from django.urls import reverse
from django.utils.timezone import now
from django_celery_beat.models import ClockedSchedule
from model_bakery import baker

from core.models import Group, User
from counter.baker_recipes import counter_recipe, product_recipe
from counter.forms import ScheduledProductActionForm, ScheduledProductActionFormSet
from counter.models import ScheduledProductAction


@pytest.mark.django_db
def test_edit_product(client: Client):
    client.force_login(
        baker.make(
            User, groups=[Group.objects.get(id=settings.SITH_GROUP_COUNTER_ADMIN_ID)]
        )
    )
    product = product_recipe.make()
    url = reverse("counter:product_edit", kwargs={"product_id": product.id})
    res = client.get(url)
    assert res.status_code == 200

    res = client.post(url, data={})
    # This is actually a failure, but we just want to check that
    # we don't have a 403 or a 500.
    # The actual behaviour will be tested directly on the form.
    assert res.status_code == 200


@pytest.mark.django_db
class TestProductActionForm:
    def test_single_form_archive(self):
        product = product_recipe.make()
        trigger_at = now() + timedelta(minutes=10)
        form = ScheduledProductActionForm(
            product=product,
            data={
                "scheduled-task": "counter.tasks.archive_product",
                "scheduled-trigger_at": trigger_at,
            },
        )
        assert form.is_valid()
        instance = form.save()
        assert instance.clocked.clocked_time == trigger_at
        assert instance.enabled is True
        assert instance.one_off is True
        assert instance.task == "counter.tasks.archive_product"
        assert instance.kwargs == json.dumps({"product_id": product.id})

    def test_single_form_change_counters(self):
        product = product_recipe.make()
        counter = counter_recipe.make()
        trigger_at = now() + timedelta(minutes=10)
        form = ScheduledProductActionForm(
            product=product,
            data={
                "scheduled-task": "counter.tasks.change_counters",
                "scheduled-trigger_at": trigger_at,
                "scheduled-counters": [counter.id],
            },
        )
        assert form.is_valid()
        instance = form.save()
        instance.refresh_from_db()
        assert instance.clocked.clocked_time == trigger_at
        assert instance.enabled is True
        assert instance.one_off is True
        assert instance.task == "counter.tasks.change_counters"
        assert instance.kwargs == json.dumps(
            {"product_id": product.id, "counters": [counter.id]}
        )

    def test_delete(self):
        product = product_recipe.make()
        clocked = baker.make(ClockedSchedule, clocked_time=now() + timedelta(minutes=2))
        task = baker.make(
            ScheduledProductAction,
            product=product,
            one_off=True,
            clocked=clocked,
            task="counter.tasks.archive_product",
        )
        formset = ScheduledProductActionFormSet(product=product)
        formset.delete_existing(task)
        assert not ScheduledProductAction.objects.filter(id=task.id).exists()
        assert not ClockedSchedule.objects.filter(id=clocked.id).exists()


@pytest.mark.django_db
class TestProductActionFormSet:
    def test_ok(self):
        product = product_recipe.make()
        counter = counter_recipe.make()
        trigger_at = now() + timedelta(minutes=10)
        formset = ScheduledProductActionFormSet(
            product=product,
            data={
                "form-TOTAL_FORMS": "2",
                "form-INITIAL_FORMS": "0",
                "form-0-task": "counter.tasks.archive_product",
                "form-0-trigger_at": trigger_at,
                "form-1-task": "counter.tasks.change_counters",
                "form-1-trigger_at": trigger_at,
                "form-1-counters": [counter.id],
            },
        )
        assert formset.is_valid()
        formset.save()
        assert ScheduledProductAction.objects.filter(product=product).count() == 2
