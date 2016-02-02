import os
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.conf import settings


from core.models import Group, User, Page, PageRev
from accounting.models import Customer, GeneralJournal, ProductType, Product
from club.models import Club
from subscription.models import Subscription, Subscriber

class Command(BaseCommand):
    help = "Set up a new instance of the Sith AE"

    def add_arguments(self, parser):
        parser.add_argument('--prod', action="store_true")

    def handle(self, *args, **options):
        try:
            os.unlink(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'db.sqlite3'))
            os.mkdir(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))+'/data')
        except Exception as e:
            print(e)
        call_command('migrate')
        u = User(username='root', last_name="", first_name="Bibou",
                 email="ae.info@utbm.fr",
                 date_of_birth="1942-06-12",
                 is_superuser=True, is_staff=True)
        u.set_password("plop")
        u.save()
        for g in settings.AE_GROUPS.values():
            Group(id=g['id'], name=g['name']).save()
        ae = Club(name=settings.AE_MAIN_CLUB['name'], unix_name=settings.AE_MAIN_CLUB['unix_name'],
                address=settings.AE_MAIN_CLUB['address'])
        ae.save()

        # Here we add a lot of test datas, that are not necessary for the Sith, but that provide a basic development environment
        if not options['prod']:
            print("Dev mode, adding some test data")
            s = User(username='skia', last_name="Kia", first_name="S'",
                     email="skia@git.an",
                     date_of_birth="1942-06-12",
                     is_superuser=True, is_staff=True)
            s.set_password("plop")
            s.save()
            u = User(username='guy', last_name="Carlier", first_name="Guy",
                     email="guy@git.an",
                     date_of_birth="1942-06-12",
                     is_superuser=False, is_staff=False)
            u.set_password("plop")
            u.save()
            p = Page(name='Aide_sur_la_syntaxe')
            p.set_lock(s)
            p.save()
            PageRev(page=p, title="Aide sur la syntaxe", author=s, content="""
Cette page vise à documenter la syntaxe *Markdown* utilisée sur le site.
""").save()

            # Accounting test values:
            Customer(user=s, account_id="6568j").save()
            p = ProductType(name="Bières bouteilles")
            p.save()
            Product(name="Barbar", code="BARB", product_type=p, purchase_price="1.50", selling_price="1.7",
                    special_selling_price="1.6").save()
            GeneralJournal(start_date="2015-06-12", name="A15").save()

            # Subscription
            Subscription(member=Subscriber.objects.filter(pk=s.pk).first(), subscription_type=list(settings.AE_SUBSCRIPTIONS.keys())[0],
                    payment_method=settings.AE_PAYMENT_METHOD[0]).save()

            Club(name="Bibo'UT", unix_name="bibout",
                    address="46 de la Boustifaille", parent=ae).save()
            guyut = Club(name="Guy'UT", unix_name="guyut",
                    address="42 de la Boustifaille", parent=ae)
            guyut.save()
            Club(name="Woenzel'UT", unix_name="woenzel",
                    address="Woenzel", parent=guyut).save()
            Club(name="BdF", unix_name="bdf",
                    address="Guyéuéyuéyuyé").save()
