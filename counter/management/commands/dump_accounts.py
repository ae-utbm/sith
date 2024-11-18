from collections.abc import Iterable
from operator import attrgetter

from django.conf import settings
from django.core.mail import send_mass_mail
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Exists, OuterRef, QuerySet
from django.template.loader import render_to_string
from django.utils.timezone import now
from django.utils.translation import gettext as _

from core.models import User, UserQuerySet
from counter.models import AccountDump, Counter, Customer, Selling


class Command(BaseCommand):
    """Effectively dump the inactive users.

    Users who received a warning mail enough time ago will
    have their account emptied, unless they reactivated their
    account in the meantime (e.g. by resubscribing).

    This command should be automated with a cron task.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Don't do anything, just display the number of users concerned",
        )

    def handle(self, *args, **options):
        users = self._get_users()
        # some users may have resubscribed or performed a purchase
        # (which reactivates the account).
        # Those reactivated users are not to be mailed about their account dump.
        # Instead, the related AccountDump row will be dropped,
        # as if nothing ever happened.
        # Refunding a user implies a transaction, so refunded users
        # count as reactivated users
        users_to_dump_qs = users.filter_inactive()
        reactivated_users = list(users.difference(users_to_dump_qs))
        users_to_dump = list(users_to_dump_qs)
        self.stdout.write(
            f"{len(reactivated_users)} users have reactivated their account"
        )
        self.stdout.write(f"{len(users_to_dump)} users will see their account dumped")

        if options["dry_run"]:
            return

        AccountDump.objects.ongoing().filter(
            customer__user__in=reactivated_users
        ).delete()
        self._dump_accounts({u.customer for u in users_to_dump})
        self._send_mails(users_to_dump)
        self.stdout.write("Finished !")

    @staticmethod
    def _get_users() -> UserQuerySet:
        """Fetch the users which have a pending account dump."""
        threshold = now() - settings.SITH_ACCOUNT_DUMP_DELTA
        ongoing_dump_operations: QuerySet[AccountDump] = (
            AccountDump.objects.ongoing()
            .filter(customer__user=OuterRef("pk"), warning_mail_sent_at__lt=threshold)
        )  # fmt: off
        # cf. https://github.com/astral-sh/ruff/issues/14103
        return (
            User.objects.filter(Exists(ongoing_dump_operations))
            .annotate(
                warning_date=ongoing_dump_operations.values("warning_mail_sent_at")
            )
            .select_related("customer")
        )

    @staticmethod
    @transaction.atomic
    def _dump_accounts(accounts: set[Customer]):
        """Perform the actual db operations to dump the accounts.

        An account dump completion is a two steps process:
            - create a special sale which price is equal
              to the money in the account
            - update the pending account dump operation
              by linking it to the aforementioned sale

        Args:
            accounts: the customer accounts which must be emptied
        """
        # Dump operations are special sales,
        # which price is equal to the money the user has.
        # They are made in a special counter (which should belong to the AE).
        # However, they are not linked to a product, because it would
        # make no sense to have a product without price.
        customer_ids = [account.pk for account in accounts]
        pending_dumps: list[AccountDump] = list(
            AccountDump.objects.ongoing()
            .filter(customer_id__in=customer_ids)
            .order_by("customer_id")
        )
        if len(pending_dumps) != len(customer_ids):
            raise ValueError("One or more accounts were not engaged in a dump process")
        counter = Counter.objects.get(pk=settings.SITH_COUNTER_ACCOUNT_DUMP_ID)
        sales = Selling.objects.bulk_create(
            [
                Selling(
                    label="Vidange compte inactif",
                    club=counter.club,
                    counter=counter,
                    seller=None,
                    product=None,
                    customer=account,
                    quantity=1,
                    unit_price=account.amount,
                    date=now(),
                    is_validated=True,
                )
                for account in accounts
            ]
        )
        sales.sort(key=attrgetter("customer_id"))

        # dumps and sales are linked to the same customers
        # and or both ordered with the same key, so zipping them is valid
        for dump, sale in zip(pending_dumps, sales):
            dump.dump_operation = sale
        AccountDump.objects.bulk_update(pending_dumps, ["dump_operation"])

        # Because the sales were created with a bull_create,
        # the account amounts haven't been updated,
        # which mean we must do it explicitly
        Customer.objects.filter(pk__in=customer_ids).update(amount=0)

    @staticmethod
    def _send_mails(users: Iterable[User]):
        """Send the mails informing users that their account has been dumped."""
        mails = [
            (
                _("Your AE account has been emptied"),
                render_to_string("counter/mails/account_dump.jinja", {"user": user}),
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
            )
            for user in users
        ]
        send_mass_mail(mails)
