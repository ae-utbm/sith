import requests
from django.conf import settings
from django.core.management import BaseCommand
from django.db.models import Max
from django.utils import timezone

from antispam.models import ToxicDomain


class Command(BaseCommand):
    """Update blocked ips/mails database"""

    help = "Update blocked ips/mails database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force", action="store_true", help="Force re-creation even if up to date"
        )

    def _should_update(self, *, force: bool = False) -> bool:
        if force:
            return True
        oldest = ToxicDomain.objects.filter(is_externally_managed=True).aggregate(
            res=Max("created")
        )["res"]
        return not (oldest and timezone.now() < (oldest + timezone.timedelta(days=1)))

    def _download_domains(self, providers: list[str]) -> set[str]:
        domains = set()
        for provider in providers:
            res = requests.get(provider)
            if not res.ok:
                self.stderr.write(
                    f"Source {provider} responded with code {res.status_code}"
                )
                continue
            domains |= set(res.text.splitlines())
        return domains

    def _update_domains(self, domains: set[str]):
        # Cleanup database
        ToxicDomain.objects.filter(is_externally_managed=True).delete()

        # Create database
        ToxicDomain.objects.bulk_create(
            [
                ToxicDomain(domain=domain, is_externally_managed=True)
                for domain in domains
            ],
            ignore_conflicts=True,
        )
        self.stdout.write("Domain database updated")

    def handle(self, *args, **options):
        if not self._should_update(force=options["force"]):
            self.stdout.write("Domain database is up to date")
            return
        self.stdout.write("Updating domain database")

        domains = self._download_domains(settings.TOXIC_DOMAINS_PROVIDERS)

        if not domains:
            self.stderr.write(
                "No domains could be fetched from settings.TOXIC_DOMAINS_PROVIDERS. "
                "Please, have a look at your settings."
            )
            return

        self._update_domains(domains)
