import os
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.conf import settings


from core.models import Group, User, Page, PageRev
from accounting.models import GeneralJournal, BankAccount, ClubAccount, Operation, AccountingType
from club.models import Club, Membership
from subscription.models import Subscription, Subscriber
from counter.models import Customer, ProductType, Product, Counter

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
            skia = User(username='skia', last_name="Kia", first_name="S'",
                     email="skia@git.an",
                     date_of_birth="1942-06-12")
            skia.set_password("plop")
            skia.save()
            skia.view_groups=[Group.objects.filter(name=settings.SITH_MAIN_MEMBERS_GROUP).first().id]
            skia.save()
            # Adding user public
            public = User(username='public', last_name="Not subscribed", first_name="Public",
                     email="public@git.an",
                     date_of_birth="1942-06-12",
                     is_superuser=False, is_staff=False)
            public.set_password("plop")
            public.save()
            public.view_groups=[Group.objects.filter(name=settings.SITH_MAIN_MEMBERS_GROUP).first().id]
            public.save()
            # Adding user Subscriber
            subscriber = User(username='subscriber', last_name="User", first_name="Subscribed",
                     email="Subscribed@git.an",
                     date_of_birth="1942-06-12",
                     is_superuser=False, is_staff=False)
            subscriber.set_password("plop")
            subscriber.save()
            subscriber.view_groups=[Group.objects.filter(name=settings.SITH_MAIN_MEMBERS_GROUP).first().id]
            subscriber.save()
            # Adding user Comptable
            comptable = User(username='comptable', last_name="Able", first_name="Compte",
                     email="compta@git.an",
                     date_of_birth="1942-06-12",
                     is_superuser=False, is_staff=False)
            comptable.set_password("plop")
            comptable.save()
            comptable.view_groups=[Group.objects.filter(name=settings.SITH_MAIN_MEMBERS_GROUP).first().id]
            comptable.groups=[Group.objects.filter(name=settings.SITH_GROUPS['accounting-admin']['name']).first().id]
            comptable.save()
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
            PageRev(page=p, title="Aide sur la syntaxe", author=skia, content="""
Cette page vise à documenter la syntaxe *Markdown* utilisée sur le site.
""").save()
            # Adding README
            p = Page(name='README')
            p.save()
            p.view_groups=[settings.SITH_GROUPS['public']['id']]
            p.set_lock(skia)
            p.save()
            with open(os.path.join(root_path)+'/README.md', 'r') as rm:
                PageRev(page=p, title="REAMDE", author=skia, content=rm.read()).save()

            # Subscription
            ## Skia
            Subscription(member=Subscriber.objects.filter(pk=skia.pk).first(), subscription_type=list(settings.SITH_SUBSCRIPTIONS.keys())[0],
                    payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0]).save()
            ## Comptable
            Subscription(member=Subscriber.objects.filter(pk=comptable.pk).first(), subscription_type=list(settings.SITH_SUBSCRIPTIONS.keys())[0],
                    payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0]).save()
            ## Richard
            Subscription(member=Subscriber.objects.filter(pk=r.pk).first(), subscription_type=list(settings.SITH_SUBSCRIPTIONS.keys())[0],
                    payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0]).save()
            ## Subscriber
            Subscription(member=Subscriber.objects.filter(pk=subscriber.pk).first(), subscription_type=list(settings.SITH_SUBSCRIPTIONS.keys())[0],
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
            Membership(user=skia, club=ae, role=3, description="").save()
            troll = Club(name="Troll Penché", unix_name="troll",
                    address="Terre Du Milieu", parent=ae)
            troll.save()

            # Counters
            Customer(user=skia, account_id="6568j", amount=0).save()
            p = ProductType(name="Bières bouteilles")
            p.save()
            barb = Product(name="Barbar", code="BARB", product_type=p, purchase_price="1.50", selling_price="1.7",
                    special_selling_price="1.6", club=ae)
            barb.save()
            cble = Product(name="Chimay Bleue", code="CBLE", product_type=p, purchase_price="1.50", selling_price="1.7",
                    special_selling_price="1.6", club=ae)
            cble.save()
            Product(name="Corsendonk", code="CORS", product_type=p, purchase_price="1.50", selling_price="1.7",
                    special_selling_price="1.6", club=ae).save()
            Product(name="Carolus", code="CARO", product_type=p, purchase_price="1.50", selling_price="1.7",
                    special_selling_price="1.6", club=ae).save()
            mde = Counter(name="MDE", club=ae, type="BAR")
            mde.save()
            mde.products.add(barb)
            mde.products.add(cble)
            mde.save()

            # Accounting test values:
            BankAccount(name="AE TG", club=ae).save()
            BankAccount(name="Carte AE", club=ae).save()
            ba = BankAccount(name="AE TI", club=ae)
            ba.save()
            ca = ClubAccount(name="Troll Penché", bank_account=ba, club=troll)
            ca.save()
            AccountingType(code=666, label="Guy credit", movement_type='credit').save()
            AccountingType(code=4000, label="Guy debit", movement_type='debit').save()

