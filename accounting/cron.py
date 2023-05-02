from django.core.mail import send_mail

from core.models import User
from counter.models import Customer

from datetime import date
from sith.settings import SITH_ACCOUNTING_DELTA_NOTIFICATION, SITH_ACCOUNTING_DELTA_DUMP


def dump_account_balance():
    """
    1. Récupérer la liste des comptes purgeables dans 2 mois (càd dernière cotisation > 2 ans | date de fin de cotisation <= )
    2. Leur envoyer un mail de notification
      a. Remplir le mail avec les données adéquates
      b. Enregistrer la date d'envoi du mail
    3. Pour les comptes qui ont déjà eu le rappel d'envoyé (càd, mail envoyé à la date T-2mois)
      a. Regarder le montant du compte, et le vider si le montant est non nul
      b. Envoyer le mail de notification si le montant est non nul
    """
    users_to_notify = User.objects.filter(
        customer__amount__gt=0,
        subscriptions__subscription_end__lte=date.today()
        - SITH_ACCOUNTING_DELTA_NOTIFICATION,
    )

    print(users_to_notify)

    print("Test Test")
    send_mail(
        "Subject here",
        "Here is the message.",
        "from@example.com",
        ["to@example.com"],
        fail_silently=False,
    )
