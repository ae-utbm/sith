from collections.abc import Iterable
from datetime import timedelta

import freezegun
import pytest
from django.conf import settings
from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.utils.timezone import now
from model_bakery import baker
from model_bakery.recipe import Recipe

from core.baker_recipes import subscriber_user, very_old_subscriber_user
from counter.management.commands.dump_accounts import Command as DumpCommand
from counter.management.commands.dump_warning_mail import Command as WarningCommand
from counter.models import AccountDump, Customer, Refilling, Selling
from subscription.models import Subscription


class TestAccountDump(TestCase):
    @classmethod
    def set_up_notified_users(cls):
        """Create the users which should be considered as dumpable"""
        cls.notified_users = very_old_subscriber_user.make(_quantity=3)
        baker.make(
            Refilling,
            amount=10,
            customer=(u.customer for u in cls.notified_users),
            date=now() - settings.SITH_ACCOUNT_INACTIVITY_DELTA - timedelta(days=1),
            _quantity=len(cls.notified_users),
        )

    @classmethod
    def set_up_not_notified_users(cls):
        """Create the users which should not be considered as dumpable"""
        refill_recipe = Recipe(Refilling, amount=10)
        cls.not_notified_users = [
            subscriber_user.make(),
            very_old_subscriber_user.make(),  # inactive, but account already empty
            very_old_subscriber_user.make(),  # inactive, but with a recent transaction
            very_old_subscriber_user.make(),  # inactive, but already warned
        ]
        refill_recipe.make(
            customer=cls.not_notified_users[2].customer, date=now() - timedelta(days=1)
        )
        refill_recipe.make(
            customer=cls.not_notified_users[3].customer,
            date=now() - settings.SITH_ACCOUNT_INACTIVITY_DELTA - timedelta(days=1),
        )
        baker.make(
            AccountDump,
            customer=cls.not_notified_users[3].customer,
            dump_operation=None,
        )


class TestAccountDumpWarningMailCommand(TestAccountDump):
    @classmethod
    def setUpTestData(cls):
        # delete existing accounts to avoid side effect
        Customer.objects.all().delete()
        cls.set_up_notified_users()
        cls.set_up_not_notified_users()

    def test_user_selection(self):
        """Test that the user to warn are well selected."""
        users = list(WarningCommand._get_users())
        assert len(users) == len(self.notified_users)
        assert set(users) == set(self.notified_users)

    def test_command(self):
        """The actual command test."""
        call_command("dump_warning_mail")
        # 1 already existing + 3 new account dump objects
        assert AccountDump.objects.count() == 4
        sent_mails = list(mail.outbox)
        assert len(sent_mails) == 3
        target_emails = {u.email for u in self.notified_users}
        for sent in sent_mails:
            assert len(sent.to) == 1
            assert sent.to[0] in target_emails


class TestAccountDumpCommand(TestAccountDump):
    @classmethod
    def setUpTestData(cls):
        with freezegun.freeze_time(
            now() - settings.SITH_ACCOUNT_DUMP_DELTA - timedelta(hours=1)
        ):
            # pretend the notifications happened enough time ago
            # to make sure the accounts are dumpable right now
            cls.set_up_notified_users()
            AccountDump.objects.bulk_create(
                [
                    AccountDump(customer=u.customer, warning_mail_sent_at=now())
                    for u in cls.notified_users
                ]
            )
        # One of the users reactivated its account
        baker.make(
            Subscription,
            member=cls.notified_users[0],
            subscription_start=now() - timedelta(days=1),
        )

    def assert_accounts_dumped(self, accounts: Iterable[Customer]):
        """Assert that the given accounts have been dumped"""
        assert not (
            AccountDump.objects.ongoing().filter(customer__in=accounts).exists()
        )
        for customer in accounts:
            initial_amount = customer.amount
            customer.refresh_from_db()
            assert customer.amount == 0
            operation: Selling = customer.buyings.order_by("date").last()
            assert operation.unit_price == initial_amount
            assert operation.counter_id == settings.SITH_COUNTER_ACCOUNT_DUMP_ID
            assert operation.is_validated is True
            dump = customer.dumps.last()
            assert dump.dump_operation == operation

    def test_user_selection(self):
        """Test that users to dump are well selected"""
        # even reactivated users should be selected,
        # because their pending AccountDump must be dealt with
        users = list(DumpCommand._get_users())
        assert len(users) == len(self.notified_users)
        assert set(users) == set(self.notified_users)

    def test_dump_accounts(self):
        """Test the _dump_accounts method"""
        # the first user reactivated its account, thus should not be dumped
        to_dump: set[Customer] = {u.customer for u in self.notified_users[1:]}
        DumpCommand._dump_accounts(to_dump)
        self.assert_accounts_dumped(to_dump)

    def test_dump_account_with_active_users(self):
        """Test that the dump account method failed if given active users."""
        active_user = subscriber_user.make()
        active_user.customer.amount = 10
        active_user.customer.save()
        customers = {u.customer for u in self.notified_users}
        customers.add(active_user.customer)
        with pytest.raises(ValueError):
            DumpCommand._dump_accounts(customers)
        for customer in customers:
            # all users should have kept their money
            initial_amount = customer.amount
            customer.refresh_from_db()
            assert customer.amount == initial_amount

    def test_command(self):
        """test the actual command"""
        call_command("dump_accounts")
        reactivated_user = self.notified_users[0]
        # the pending operation should be deleted for reactivated users
        assert not reactivated_user.customer.dumps.exists()
        assert reactivated_user.customer.amount == 10

        dumped_users = self.notified_users[1:]
        self.assert_accounts_dumped([u.customer for u in dumped_users])
        sent_mails = list(mail.outbox)
        assert len(sent_mails) == 2
        target_emails = {u.email for u in dumped_users}
        for sent in sent_mails:
            assert len(sent.to) == 1
            assert sent.to[0] in target_emails
