import os
from datetime import date, datetime
from io import StringIO

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.conf import settings
from django.db import connection
from django.contrib.sites.models import Site


from core.models import Group, User, Page, PageRev, SithFile
from accounting.models import GeneralJournal, BankAccount, ClubAccount, Operation, AccountingType, SimplifiedAccountingType, Company
from club.models import Club, Membership
from subscription.models import Subscription
from counter.models import Customer, ProductType, Product, Counter
from com.models import Sith
from election.models import Election, Role, Candidature, List

class Command(BaseCommand):
    help = "Populate a new instance of the Sith AE"

    def add_arguments(self, parser):
        parser.add_argument('--prod', action="store_true")

    def reset_index(self, *args):
        sqlcmd = StringIO()
        call_command("sqlsequencereset", *args, stdout=sqlcmd)
        cursor = connection.cursor()
        cursor.execute(sqlcmd.getvalue())

    def handle(self, *args, **options):
        os.environ['DJANGO_COLORS'] = 'nocolor'
        Site(id=4000, domain=settings.SITH_URL, name=settings.SITH_NAME).save()
        root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        Group(name="Root").save()
        Group(name="Not registered users").save()
        Group(name="Accounting admin").save()
        Group(name="Communication admin").save()
        Group(name="Counter admin").save()
        Group(name="Banned from buying alcohol").save()
        Group(name="Banned from counters").save()
        Group(name="Banned to subscribe").save()
        Group(name="SAS admin").save()
        self.reset_index("core", "auth")
        root = User(id=0, username='root', last_name="", first_name="Bibou",
                 email="ae.info@utbm.fr",
                 date_of_birth="1942-06-12",
                 is_superuser=True, is_staff=True)
        root.set_password("plop")
        root.save()
        SithFile(parent=None, name="profiles", is_folder=True, owner=root).save()
        home_root = SithFile(parent=None, name="users", is_folder=True, owner=root)
        home_root.save()
        club_root = SithFile(parent=None, name="clubs", is_folder=True, owner=root)
        club_root.save()
        SithFile(parent=None, name="SAS", is_folder=True, owner=root).save()
        main_club = Club(id=1, name=settings.SITH_MAIN_CLUB['name'], unix_name=settings.SITH_MAIN_CLUB['unix_name'],
                address=settings.SITH_MAIN_CLUB['address'])
        main_club.save()
        bar_club = Club(id=2, name=settings.SITH_BAR_MANAGER['name'], unix_name=settings.SITH_BAR_MANAGER['unix_name'],
                address=settings.SITH_BAR_MANAGER['address'])
        bar_club.save()
        launderette_club = Club(id=84, name=settings.SITH_LAUNDERETTE_MANAGER['name'],
                unix_name=settings.SITH_LAUNDERETTE_MANAGER['unix_name'],
                address=settings.SITH_LAUNDERETTE_MANAGER['address'])
        launderette_club.save()
        self.reset_index("club")
        for b in settings.SITH_COUNTER_BARS:
            g = Group(name=b[1]+" admin")
            g.save()
            c = Counter(id=b[0], name=b[1], club=bar_club, type='BAR')
            c.save()
            c.edit_groups = [g]
            c.save()
        self.reset_index("counter")
        Counter(name="Eboutic", club=main_club, type='EBOUTIC').save()
        Counter(name="AE", club=main_club, type='OFFICE').save()

        home_root.view_groups = [Group.objects.filter(name=settings.SITH_MAIN_MEMBERS_GROUP).first()]
        club_root.view_groups = [Group.objects.filter(name=settings.SITH_MAIN_MEMBERS_GROUP).first()]
        home_root.save()
        club_root.save()

        Sith().save()

        p = Page(name='Index')
        p.set_lock(root)
        p.save()
        p.view_groups=[settings.SITH_GROUP_PUBLIC_ID]
        p.set_lock(root)
        p.save()
        PageRev(page=p, title="Wiki index", author=root, content="""
Welcome to the wiki page!
""").save()

        p = Page(name="services")
        p.set_lock(root)
        p.save()
        p.view_groups=[settings.SITH_GROUP_PUBLIC_ID]
        p.set_lock(root)
        PageRev(page=p, title="Services", author=root, content="""
|   |   |   |
| :---: | :---: | :---: | :---: |
| [Eboutic](/eboutic) | [Laverie](/launderette) | Matmat | [Fichiers](/file) |
| SAS | Weekmail | Forum | |

""").save()

        p = Page(name="launderette")
        p.set_lock(root)
        p.save()
        p.set_lock(root)
        PageRev(page=p, title="Laverie", author=root, content="Fonctionnement de la laverie").save()

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
            # Adding user Counter admin
            counter = User(username='counter', last_name="Ter", first_name="Coun",
                     email="counter@git.an",
                     date_of_birth="1942-06-12",
                     is_superuser=False, is_staff=False)
            counter.set_password("plop")
            counter.save()
            counter.view_groups=[Group.objects.filter(name=settings.SITH_MAIN_MEMBERS_GROUP).first().id]
            counter.groups=[Group.objects.filter(id=settings.SITH_GROUP_COUNTER_ADMIN_ID).first().id]
            counter.save()
            # Adding user Comptable
            comptable = User(username='comptable', last_name="Able", first_name="Compte",
                     email="compta@git.an",
                     date_of_birth="1942-06-12",
                     is_superuser=False, is_staff=False)
            comptable.set_password("plop")
            comptable.save()
            comptable.view_groups=[Group.objects.filter(name=settings.SITH_MAIN_MEMBERS_GROUP).first().id]
            comptable.groups=[Group.objects.filter(id=settings.SITH_GROUP_ACCOUNTING_ADMIN_ID).first().id]
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
            p.save(force_lock=True)
            PageRev(page=p, title="Aide sur la syntaxe", author=skia, content="""
Cette page vise à documenter la syntaxe *Markdown* utilisée sur le site.
""").save()
            p = Page(name='Services')
            p.save(force_lock=True)
            p.view_groups=[settings.SITH_GROUP_PUBLIC_ID]
            p.save(force_lock=True)
            PageRev(page=p, title="Services", author=skia, content="""
|   |   |   |
| :---: | :---: | :---: |
| [Eboutic](/eboutic) | [Laverie](/launderette) | Matmat |
| SAS | Weekmail | Forum|

""").save()
            # Adding README
            p = Page(name='README')
            p.save(force_lock=True)
            p.view_groups=[settings.SITH_GROUP_PUBLIC_ID]
            p.save(force_lock=True)
            with open(os.path.join(root_path)+'/README.md', 'r') as rm:
                PageRev(page=p, title="README", author=skia, content=rm.read()).save()

            # Subscription
            ## Root
            s = Subscription(member=User.objects.filter(pk=root.pk).first(), subscription_type=list(settings.SITH_SUBSCRIPTIONS.keys())[0],
                    payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0])
            s.subscription_start = s.compute_start()
            s.subscription_end = s.compute_end(
                    duration=settings.SITH_SUBSCRIPTIONS[s.subscription_type]['duration'],
                    start=s.subscription_start)
            s.save()
            ## Skia
            s = Subscription(member=User.objects.filter(pk=skia.pk).first(), subscription_type=list(settings.SITH_SUBSCRIPTIONS.keys())[0],
                    payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0])
            s.subscription_start = s.compute_start()
            s.subscription_end = s.compute_end(
                    duration=settings.SITH_SUBSCRIPTIONS[s.subscription_type]['duration'],
                    start=s.subscription_start)
            s.save()
            ## Comptable
            s = Subscription(member=User.objects.filter(pk=comptable.pk).first(), subscription_type=list(settings.SITH_SUBSCRIPTIONS.keys())[0],
                    payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0])
            s.subscription_start = s.compute_start()
            s.subscription_end = s.compute_end(
                    duration=settings.SITH_SUBSCRIPTIONS[s.subscription_type]['duration'],
                    start=s.subscription_start)
            s.save()
            ## Richard
            s = Subscription(member=User.objects.filter(pk=r.pk).first(), subscription_type=list(settings.SITH_SUBSCRIPTIONS.keys())[0],
                    payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0])
            s.subscription_start = s.compute_start()
            s.subscription_end = s.compute_end(
                    duration=settings.SITH_SUBSCRIPTIONS[s.subscription_type]['duration'],
                    start=s.subscription_start)
            s.save()
            ## User
            s = Subscription(member=User.objects.filter(pk=subscriber.pk).first(), subscription_type=list(settings.SITH_SUBSCRIPTIONS.keys())[0],
                    payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0])
            s.subscription_start = s.compute_start()
            s.subscription_end = s.compute_end(
                    duration=settings.SITH_SUBSCRIPTIONS[s.subscription_type]['duration'],
                    start=s.subscription_start)
            s.save()

            # Clubs
            Club(name="Bibo'UT", unix_name="bibout",
                    address="46 de la Boustifaille", parent=main_club).save()
            guyut = Club(name="Guy'UT", unix_name="guyut",
                    address="42 de la Boustifaille", parent=main_club)
            guyut.save()
            Club(name="Woenzel'UT", unix_name="woenzel",
                    address="Woenzel", parent=guyut).save()
            Membership(user=skia, club=main_club, role=3, description="").save()
            troll = Club(name="Troll Penché", unix_name="troll",
                    address="Terre Du Milieu", parent=main_club)
            troll.save()
            refound = Club(name="Carte AE", unix_name="carte_ae",
                    address="Jamais imprimée", parent=main_club)
            refound.save()

            # Counters
            Customer(user=skia, account_id="6568j", amount=0).save()
            Customer(user=r, account_id="4000", amount=0).save()
            p = ProductType(name="Bières bouteilles")
            p.save()
            barb = Product(name="Barbar", code="BARB", product_type=p, purchase_price="1.50", selling_price="1.7",
                    special_selling_price="1.6", club=main_club)
            barb.save()
            cble = Product(name="Chimay Bleue", code="CBLE", product_type=p, purchase_price="1.50", selling_price="1.7",
                    special_selling_price="1.6", club=main_club)
            cble.save()
            Product(name="Corsendonk", code="CORS", product_type=p, purchase_price="1.50", selling_price="1.7",
                    special_selling_price="1.6", club=main_club).save()
            Product(name="Carolus", code="CARO", product_type=p, purchase_price="1.50", selling_price="1.7",
                    special_selling_price="1.6", club=main_club).save()
            mde = Counter.objects.filter(name="MDE").first()
            mde.products.add(barb)
            mde.products.add(cble)
            mde.save()

            refound_counter = Counter(name="Carte AE", club=refound, type='OFFICE')
            refound_counter.save()
            refound_product = Product(name="remboursement", code="REMBOURS", purchase_price="0", selling_price="0",
                    special_selling_price="0", club=refound)
            refound_product.save()

            # Accounting test values:
            BankAccount(name="AE TG", club=main_club).save()
            BankAccount(name="Carte AE", club=main_club).save()
            ba = BankAccount(name="AE TI", club=main_club)
            ba.save()
            ca = ClubAccount(name="Troll Penché", bank_account=ba, club=troll)
            ca.save()
            gj = GeneralJournal(name="A16", start_date=date.today(), club_account=ca)
            gj.save()
            credit = AccountingType(code='74', label="Subventions d'exploitation", movement_type='CREDIT')
            credit.save()
            debit = AccountingType(code='606', label="Achats non stockés de matières et fournitures(*1)", movement_type='DEBIT')
            debit.save()
            debit2 = AccountingType(code='604', label="Achats d'études et prestations de services(*2)", movement_type='DEBIT')
            debit2.save()
            buying = AccountingType(code='60', label="Achats (sauf 603)", movement_type='DEBIT')
            buying.save()
            comptes = AccountingType(code='6', label="Comptes de charge", movement_type='DEBIT')
            comptes.save()
            simple = SimplifiedAccountingType(label = 'Je fais du simple 6', accounting_type = comptes, movement_type='DEBIT')
            simple.save()
            woenzco = Company(name="Woenzel & co")
            woenzco.save()
            # Adding user sli
            sli = User(username='sli', last_name="Li", first_name="S",
                       email="sli@git.an",
                       date_of_birth="1942-06-12")
            sli.set_password("plop")
            sli.save()
            skia.view_groups=[Group.objects.filter(name=settings.SITH_MAIN_MEMBERS_GROUP).first().id]
            sli.save()
            # Adding user Krophil
            krophil = User(username='krophil', last_name="Phil'", first_name="Kro",
                           email="krophil@git.an",
                           date_of_birth="1942-06-12")
            krophil.set_password("plop")
            krophil.save()
            ## Adding subscription for sli
            s = Subscription(member=User.objects.filter(pk=sli.pk).first(), subscription_type=list(settings.SITH_SUBSCRIPTIONS.keys())[0],
                    payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0])
            s.subscription_start = s.compute_start()
            s.subscription_end = s.compute_end(
                    duration=settings.SITH_SUBSCRIPTIONS[s.subscription_type]['duration'],
                    start=s.subscription_start)
            s.save()
            ## Adding subscription for Krophil
            s = Subscription(member=User.objects.filter(pk=krophil.pk).first(), subscription_type=list(settings.SITH_SUBSCRIPTIONS.keys())[0],
                    payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0])
            s.subscription_start = s.compute_start()
            s.subscription_end = s.compute_end(
                    duration=settings.SITH_SUBSCRIPTIONS[s.subscription_type]['duration'],
                    start=s.subscription_start)
            s.save()

            operation_list = [
                            (27, "J'avais trop de bière", 'CASH', None, buying, 'USER', skia.id, "", None), 
                            (4000, "Ceci n'est pas une opération... en fait si mais non", 'CHECK', None, debit,'COMPANY', woenzco.id, "", 23),
                            (22, "C'est de l'argent ?", 'CARD', None, credit, 'CLUB', troll.id, "", None),
                            (37, "Je paye CASH", 'CASH', None, debit2, 'OTHER', None, "tous les étudiants <3", None),
                            (300, "Paiement Guy", 'CASH', None, buying, 'USER', skia.id, "", None),
                            (32.3, "Essence", 'CASH', None, buying, 'OTHER', None, "station", None),
                            (46.42, "Allumette", 'CHECK', None, credit, 'CLUB', main_club.id, "", 57),
                            (666.42, "Subvention de far far away", 'CASH', None, comptes, 'CLUB', main_club.id, "", None),
                            (496, "Ça, c'est un 6", 'CARD', simple, None, 'USER', skia.id, "", None),
                            (17, "La Gargotte du Korrigan", 'CASH', None, debit2, 'CLUB', bar_club.id, "", None),
                            ]
            for op in operation_list:
                operation = Operation(journal=gj, date=date.today(), amount=op[0], 
                    remark=op[1], mode=op[2], done=True, simpleaccounting_type=op[3], 
                    accounting_type=op[4], target_type=op[5], target_id=op[6], 
                    target_label=op[7], cheque_number=op[8])
                operation.clean()
                operation.save()

            # Create an election
            el = Election(title="Élection 2017", description="La roue tourne", start_candidature='1942-06-12 10:28:45', end_candidature='2042-06-12 10:28:45',start_date='1942-06-12 10:28:45', end_date='7942-06-12 10:28:45')
            el.save()
            liste = List(title="Candidature Libre", election=el)
            liste.save()
            listeT = List(title="Troll", election=el)
            listeT.save()
            pres = Role(election=el, title="Président AE", description="Roi de l'AE")
            pres.save()
            resp = Role(election=el, title="Co Respo Info", description="Ghetto++")
            resp.save()
            cand = Candidature(role=resp, user=skia, liste=liste, program="Refesons le site AE")
            cand.save()
            cand = Candidature(role=resp, user=sli, liste=liste, program="Vasy je deviens mon propre adjoint")
            cand.save()
            cand = Candidature(role=resp, user=krophil, liste=listeT, program="Le Pôle Troll !")
            cand.save()
            cand = Candidature(role=pres, user=sli, liste=listeT, program="En fait j'aime pas l'info, je voulais faire GMC")
            cand.save()

