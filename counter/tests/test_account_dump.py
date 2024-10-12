from datetime import timedelta

from django.conf import settings
from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.utils.timezone import now
from model_bakery import baker
from model_bakery.recipe import Recipe

from core.baker_recipes import subscriber_user, very_old_subscriber_user
from counter.management.commands.dump_warning_mail import Command
from counter.models import AccountDump, Customer, Refilling


class TestAccountDumpWarningMailCommand(TestCase):
    @classmethod
    def setUpTestData(cls):
        # delete existing customers to avoid side effect
        Customer.objects.all().delete()
        refill_recipe = Recipe(Refilling, amount=10)
        cls.notified_users = very_old_subscriber_user.make(_quantity=3)
        inactive_date = (
            now() - settings.SITH_ACCOUNT_INACTIVITY_DELTA - timedelta(days=1)
        )
        refill_recipe.make(
            customer=(u.customer for u in cls.notified_users),
            date=inactive_date,
            _quantity=len(cls.notified_users),
        )
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
            customer=cls.not_notified_users[3].customer, date=inactive_date
        )
        baker.make(
            AccountDump,
            customer=cls.not_notified_users[3].customer,
            dump_operation=None,
        )

    def test_user_selection(self):
        """Test that the user to warn are well selected."""
        users = list(Command._get_users())
        assert len(users) == 3
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
