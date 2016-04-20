import os
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.conf import settings


from core.models import Group, User, Page, PageRev
from accounting.models import Customer, GeneralJournal, ProductType, Product, BankAccount, ClubAccount, Operation
from club.models import Club, Membership
from subscription.models import Subscription, Subscriber

class Command(BaseCommand):
    help = "Populate a new instance of the Sith AE"

    def add_arguments(self, parser):
        parser.add_argument('--prod', action="store_true")

    def handle(self, *args, **options):
        root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        root = User(username='root', last_name="", first_name="Bibou",
                 email="ae.info@utbm.fr",
                 date_of_birth="1942-06-12",
                 is_superuser=True, is_staff=True)
        root.set_password("plop")
        root.save()
        for g in settings.SITH_GROUPS.values():
            Group(id=g['id'], name=g['name']).save()
        ae = Club(name=settings.SITH_MAIN_CLUB['name'], unix_name=settings.SITH_MAIN_CLUB['unix_name'],
                address=settings.SITH_MAIN_CLUB['address'])
        ae.save()
        p = Page(name='Index')
        p.set_lock(root)
        p.save()
        p.view_groups=[settings.SITH_GROUPS['public']['id']]
        p.set_lock(root)
        p.save()
        PageRev(page=p, title="Wiki index", author=root, content="""
Welcome to the wiki page!
""").save()

        # Here we add a lot of test datas, that are not necessary for the Sith, but that provide a basic development environment
        if not options['prod']:
            # Adding user Skia
            s = User(username='skia', last_name="Kia", first_name="S'",
                     email="skia@git.an",
                     date_of_birth="1942-06-12")
            s.set_password("plop")
            s.save()
            s.view_groups=[Group.objects.filter(name=settings.SITH_MAIN_MEMBERS_GROUP).first().id]
            s.save()
            # Adding user Guy
            u = User(username='guy', last_name="Carlier", first_name="Guy",
                     email="guy@git.an",
                     date_of_birth="1942-06-12",
                     is_superuser=False, is_staff=False)
            u.set_password("plop")
            u.save()
            u.view_groups=[Group.objects.filter(name=settings.SITH_MAIN_MEMBERS_GROUP).first().id]
            u.save()
            # Adding user Richard Batsbak
            r = User(username='rbatsbak', last_name="Batsbak", first_name="Richard",
                     email="richard@git.an",
                     date_of_birth="1982-06-12")
            r.set_password("plop")
            r.save()
            r.view_groups=[Group.objects.filter(name=settings.SITH_MAIN_MEMBERS_GROUP).first().id]
            r.save()
            # Adding syntax help page
            p = Page(name='Aide_sur_la_syntaxe')
            p.save()
            PageRev(page=p, title="Aide sur la syntaxe", author=s, content="""
Cette page vise à documenter la syntaxe *Markdown* utilisée sur le site.
""").save()
            # Adding README
            p = Page(name='README')
            p.save()
            p.view_groups=[settings.SITH_GROUPS['public']['id']]
            p.set_lock(s)
            p.save()
            with open(os.path.join(root_path)+'/README.md', 'r') as rm:
                PageRev(page=p, title="REAMDE", author=s, content=rm.read()).save()

            # Subscription
            ## Skia
            Subscription(member=Subscriber.objects.filter(pk=s.pk).first(), subscription_type=list(settings.SITH_SUBSCRIPTIONS.keys())[0],
                    payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0]).save()
            ## Richard
            Subscription(member=Subscriber.objects.filter(pk=r.pk).first(), subscription_type=list(settings.SITH_SUBSCRIPTIONS.keys())[0],
                    payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0]).save()

            # Clubs
            Club(name="Bibo'UT", unix_name="bibout",
                    address="46 de la Boustifaille", parent=ae).save()
            guyut = Club(name="Guy'UT", unix_name="guyut",
                    address="42 de la Boustifaille", parent=ae)
            guyut.save()
            Club(name="Woenzel'UT", unix_name="woenzel",
                    address="Woenzel", parent=guyut).save()
            Club(name="BdF", unix_name="bdf",
                    address="Guyéuéyuéyuyé").save()
            Membership(user=s, club=ae, role=3, description="").save()
            troll = Club(name="Troll Penché", unix_name="troll",
                    address="Terre Du Milieu", parent=ae)
            troll.save()

            # Accounting test values:
            Customer(user=s, account_id="6568j").save()
            p = ProductType(name="Bières bouteilles")
            p.save()
            Product(name="Barbar", code="BARB", product_type=p, purchase_price="1.50", selling_price="1.7",
                    special_selling_price="1.6").save()
            Product(name="Chimay", code="CBLE", product_type=p, purchase_price="1.50", selling_price="1.7",
                    special_selling_price="1.6").save()
            Product(name="Corsendonk", code="CORS", product_type=p, purchase_price="1.50", selling_price="1.7",
                    special_selling_price="1.6").save()
            Product(name="Carolus", code="CARO", product_type=p, purchase_price="1.50", selling_price="1.7",
                    special_selling_price="1.6").save()
            BankAccount(name="AE TG").save()
            BankAccount(name="Carte AE").save()
            ba = BankAccount(name="AE TI")
            ba.save()
            ca = ClubAccount(name="Troll Penché", bank_account=ba, club=troll)
            ca.save()


