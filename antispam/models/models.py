from django.db import models
from django.utils.translation import gettext_lazy as _


class ToxicDomain(models.Model):
    """Domain marked as spam in public databases"""

    domain = models.URLField(_("domain"), max_length=253, primary_key=True)
    created = models.DateTimeField(auto_now_add=True)
    is_externally_managed = models.BooleanField(
        _("is externally managed"),
        default=False,
        help_text=_(
            "True if kept up-to-date using external toxic domain providers, else False"
        ),
    )

    def __str__(self) -> str:
        return self.domain
