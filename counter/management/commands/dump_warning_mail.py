import logging
import time
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db.models import Exists, OuterRef, Subquery
from django.template.loader import render_to_string
from django.utils.timezone import localdate, now
from django.utils.translation import gettext as _

from core.models import User, UserQuerySet
from counter.models import AccountDump
from subscription.models import Subscription


class Command(BaseCommand):
    """Send mail to inactive users, warning them that their account is about to be dumped.

    This command should be automated with a cron task.
    """

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger("account_dump_mail")
        self.logger.setLevel(logging.INFO)
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Do not send the mails, just display the number of users concerned",
        )
        parser.add_argument(
            "-d",
            "--delay",
            type=float,
            default=0,
            help="Delay in seconds between each mail sent",
        )

    def handle(self, *args, **options):
        users: list[User] = list(self._get_users())
        self.stdout.write(f"{len(users)} users will be warned of their account dump")
        if options["verbosity"] > 1:
            self.stdout.write("Users concerned:\n")
            self.stdout.write(
                "\n".join(
                    f"  - {user.get_display_name()} ({user.email}) : "
                    f"{user.customer.amount} €"
                    for user in users
                )
            )
        if options["dry_run"]:
            return
        dumps = []
        for user in users:
            is_success = self._send_mail(user)
            dumps.append(
                AccountDump(
                    customer_id=user.id,
                    warning_mail_sent_at=now(),
                    warning_mail_error=not is_success,
                )
            )
            if options["delay"]:
                # avoid spamming the mail server too much
                time.sleep(options["delay"])

        AccountDump.objects.bulk_create(dumps)
        self.stdout.write("Finished !")

    @staticmethod
    def _get_users() -> UserQuerySet:
        ongoing_dump_operation = AccountDump.objects.ongoing().filter(
            customer__user=OuterRef("pk")
        )
        return (
            User.objects.filter_inactive()
            .filter(customer__amount__gt=0)
            .exclude(Exists(ongoing_dump_operation))
            .annotate(
                last_subscription_date=Subquery(
                    Subscription.objects.filter(member=OuterRef("pk"))
                    .order_by("-subscription_end")
                    .values("subscription_end")[:1]
                ),
            )
            .select_related("customer")
        )

    def _send_mail(self, user: User) -> bool:
        """Send the warning email to the given user.

        Returns:
            True if the mail was successfully sent, else False
        """
        message = render_to_string(
            "counter/mails/account_dump_warning.jinja",
            {
                "balance": user.customer.amount,
                "last_subscription_date": user.last_subscription_date,
                "dump_date": localdate() + settings.SITH_ACCOUNT_DUMP_DELTA,
            },
        )
        try:
            # sending mails one by one is long and ineffective,
            # but it makes easier to know which emails failed (and how).
            # Also, there won't be that much mails sent (except on the first run)
            send_mail(
                _("Clearing of your AE account"),
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
            )
            self.logger.info(f"Mail successfully sent to {user.email}")
            return True
        except SMTPException as e:
            self.logger.error(f"failed mail to {user.email} :\n{e}")
            return False
