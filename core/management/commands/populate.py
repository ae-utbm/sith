# -*- coding:utf-8 -*
#
# Copyright 2016,2017
# - Skia <skia@libskia.so>
#
# Ce fichier fait partie du site de l'Association des Étudiants de l'UTBM,
# http://ae.utbm.fr.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License a published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Sofware Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.
#
#

import os
from datetime import date, datetime, timedelta
from io import StringIO, BytesIO

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from django.db import connection
from django.contrib.sites.models import Site
from django.utils import timezone

from PIL import Image

from core.models import Group, User, Page, PageRev, SithFile
from accounting.models import (
    GeneralJournal,
    BankAccount,
    ClubAccount,
    Operation,
    AccountingType,
    SimplifiedAccountingType,
    Company,
)
from core.utils import resize_image
from club.models import Club, Membership
from subscription.models import Subscription
from counter.models import Customer, ProductType, Product, Counter, Selling, StudentCard
from com.models import Sith, Weekmail, News, NewsDate
from election.models import Election, Role, Candidature, ElectionList
from forum.models import Forum, ForumTopic
from pedagogy.models import UV


class Command(BaseCommand):
    help = "Populate a new instance of the Sith AE"

    def add_arguments(self, parser):
        parser.add_argument("--prod", action="store_true")

    def reset_index(self, *args):
        sqlcmd = StringIO()
        call_command("sqlsequencereset", *args, stdout=sqlcmd)
        cursor = connection.cursor()
        cursor.execute(sqlcmd.getvalue())

    def handle(self, *args, **options):
        os.environ["DJANGO_COLORS"] = "nocolor"
        Site(id=4000, domain=settings.SITH_URL, name=settings.SITH_NAME).save()
        root_path = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        )
        Group(name="Root").save()
        Group(name="Public").save()
        Group(name="Subscribers").save()
        Group(name="Old subscribers").save()
        Group(name="Accounting admin").save()
        Group(name="Communication admin").save()
        Group(name="Counter admin").save()
        Group(name="Banned from buying alcohol").save()
        Group(name="Banned from counters").save()
        Group(name="Banned to subscribe").save()
        Group(name="SAS admin").save()
        Group(name="Forum admin").save()
        Group(name="Pedagogy admin").save()
        self.reset_index("core", "auth")
        root = User(
            id=0,
            username="root",
            last_name="",
            first_name="Bibou",
            email="ae.info@utbm.fr",
            date_of_birth="1942-06-12",
            is_superuser=True,
            is_staff=True,
        )
        root.set_password("plop")
        root.save()
        profiles_root = SithFile(
            parent=None, name="profiles", is_folder=True, owner=root
        )
        profiles_root.save()
        home_root = SithFile(parent=None, name="users", is_folder=True, owner=root)
        home_root.save()

        # Page needed for club creation
        p = Page(name=settings.SITH_CLUB_ROOT_PAGE)
        p.set_lock(root)
        p.save()

        club_root = SithFile(parent=None, name="clubs", is_folder=True, owner=root)
        club_root.save()
        SithFile(parent=None, name="SAS", is_folder=True, owner=root).save()
        main_club = Club(
            id=1,
            name=settings.SITH_MAIN_CLUB["name"],
            unix_name=settings.SITH_MAIN_CLUB["unix_name"],
            address=settings.SITH_MAIN_CLUB["address"],
        )
        main_club.save()
        bar_club = Club(
            id=2,
            name=settings.SITH_BAR_MANAGER["name"],
            unix_name=settings.SITH_BAR_MANAGER["unix_name"],
            address=settings.SITH_BAR_MANAGER["address"],
        )
        bar_club.save()
        launderette_club = Club(
            id=84,
            name=settings.SITH_LAUNDERETTE_MANAGER["name"],
            unix_name=settings.SITH_LAUNDERETTE_MANAGER["unix_name"],
            address=settings.SITH_LAUNDERETTE_MANAGER["address"],
        )

        launderette_club.save()
        self.reset_index("club")
        for b in settings.SITH_COUNTER_BARS:
            g = Group(name=b[1] + " admin")
            g.save()
            c = Counter(id=b[0], name=b[1], club=bar_club, type="BAR")
            c.save()
            g.editable_counters.add(c)
            g.save()
        self.reset_index("counter")
        Counter(name="Eboutic", club=main_club, type="EBOUTIC").save()
        Counter(name="AE", club=main_club, type="OFFICE").save()

        home_root.view_groups.set(
            [Group.objects.filter(name=settings.SITH_MAIN_MEMBERS_GROUP).first()]
        )
        club_root.view_groups.set(
            [Group.objects.filter(name=settings.SITH_MAIN_MEMBERS_GROUP).first()]
        )
        home_root.save()
        club_root.save()

        Sith(weekmail_destinations="etudiants@git.an personnel@git.an").save()
        Weekmail().save()

        p = Page(name="Index")
        p.set_lock(root)
        p.save()
        p.view_groups.set([settings.SITH_GROUP_PUBLIC_ID])
        p.set_lock(root)
        p.save()
        PageRev(
            page=p,
            title="Wiki index",
            author=root,
            content="""
Welcome to the wiki page!
""",
        ).save()

        p = Page(name="services")
        p.set_lock(root)
        p.save()
        p.view_groups.set([settings.SITH_GROUP_PUBLIC_ID])
        p.set_lock(root)
        PageRev(
            page=p,
            title="Services",
            author=root,
            content="""
|   |   |   |
| :---: | :---: | :---: | :---: |
| [Eboutic](/eboutic) | [Laverie](/launderette) | Matmat | [Fichiers](/file) |
| SAS | Weekmail | Forum | |

""",
        ).save()

        p = Page(name="launderette")
        p.set_lock(root)
        p.save()
        p.set_lock(root)
        PageRev(
            page=p, title="Laverie", author=root, content="Fonctionnement de la laverie"
        ).save()

        # Here we add a lot of test datas, that are not necessary for the Sith, but that provide a basic development environment
        if not options["prod"]:
            # Adding user Skia
            skia = User(
                username="skia",
                last_name="Kia",
                first_name="S'",
                email="skia@git.an",
                date_of_birth="1942-06-12",
            )
            skia.set_password("plop")
            skia.save()
            skia.view_groups = [
                Group.objects.filter(name=settings.SITH_MAIN_MEMBERS_GROUP).first().id
            ]
            skia.save()
            skia_profile_path = os.path.join(root_path, "core/fixtures/images/3.jpg")
            with open(skia_profile_path, "rb") as f:
                name = str(skia.id) + "_profile.jpg"
                skia_profile = SithFile(
                    parent=profiles_root,
                    name=name,
                    file=resize_image(Image.open(BytesIO(f.read())), 400, "JPEG"),
                    owner=skia,
                    is_folder=False,
                    mime_type="image/jpeg",
                    size=os.path.getsize(skia_profile_path),
                )
                skia_profile.file.name = name
                skia_profile.save()
                skia.profile_pict = skia_profile
                skia.save()

            # Adding user public
            public = User(
                username="public",
                last_name="Not subscribed",
                first_name="Public",
                email="public@git.an",
                date_of_birth="1942-06-12",
                is_superuser=False,
                is_staff=False,
            )
            public.set_password("plop")
            public.save()
            public.view_groups = [
                Group.objects.filter(name=settings.SITH_MAIN_MEMBERS_GROUP).first().id
            ]
            public.save()
            # Adding user Subscriber
            subscriber = User(
                username="subscriber",
                last_name="User",
                first_name="Subscribed",
                email="Subscribed@git.an",
                date_of_birth="1942-06-12",
                is_superuser=False,
                is_staff=False,
            )
            subscriber.set_password("plop")
            subscriber.save()
            subscriber.view_groups = [
                Group.objects.filter(name=settings.SITH_MAIN_MEMBERS_GROUP).first().id
            ]
            subscriber.save()
            # Adding user old Subscriber
            old_subscriber = User(
                username="old_subscriber",
                last_name="Subscriber",
                first_name="Old",
                email="old_subscriber@git.an",
                date_of_birth="1942-06-12",
                is_superuser=False,
                is_staff=False,
            )
            old_subscriber.set_password("plop")
            old_subscriber.save()
            old_subscriber.view_groups = [
                Group.objects.filter(name=settings.SITH_MAIN_MEMBERS_GROUP).first().id
            ]
            old_subscriber.save()
            # Adding user Counter admin
            counter = User(
                username="counter",
                last_name="Ter",
                first_name="Coun",
                email="counter@git.an",
                date_of_birth="1942-06-12",
                is_superuser=False,
                is_staff=False,
            )
            counter.set_password("plop")
            counter.save()
            counter.view_groups = [
                Group.objects.filter(name=settings.SITH_MAIN_MEMBERS_GROUP).first().id
            ]
            counter.groups.set(
                [
                    Group.objects.filter(id=settings.SITH_GROUP_COUNTER_ADMIN_ID)
                    .first()
                    .id
                ]
            )
            counter.save()
            # Adding user Comptable
            comptable = User(
                username="comptable",
                last_name="Able",
                first_name="Compte",
                email="compta@git.an",
                date_of_birth="1942-06-12",
                is_superuser=False,
                is_staff=False,
            )
            comptable.set_password("plop")
            comptable.save()
            comptable.view_groups = [
                Group.objects.filter(name=settings.SITH_MAIN_MEMBERS_GROUP).first().id
            ]
            comptable.groups.set(
                [
                    Group.objects.filter(id=settings.SITH_GROUP_ACCOUNTING_ADMIN_ID)
                    .first()
                    .id
                ]
            )
            comptable.save()
            # Adding user Guy
            u = User(
                username="guy",
                last_name="Carlier",
                first_name="Guy",
                email="guy@git.an",
                date_of_birth="1942-06-12",
                is_superuser=False,
                is_staff=False,
            )
            u.set_password("plop")
            u.save()
            u.view_groups = [
                Group.objects.filter(name=settings.SITH_MAIN_MEMBERS_GROUP).first().id
            ]
            u.save()
            # Adding user Richard Batsbak
            r = User(
                username="rbatsbak",
                last_name="Batsbak",
                first_name="Richard",
                email="richard@git.an",
                date_of_birth="1982-06-12",
            )
            r.set_password("plop")
            r.save()
            r.view_groups = [
                Group.objects.filter(name=settings.SITH_MAIN_MEMBERS_GROUP).first().id
            ]
            r.save()
            # Adding syntax help page
            p = Page(name="Aide_sur_la_syntaxe")
            p.save(force_lock=True)
            with open(os.path.join(root_path) + "/doc/SYNTAX.md", "r") as rm:
                PageRev(
                    page=p, title="Aide sur la syntaxe", author=skia, content=rm.read()
                ).save()
            p.view_groups.set([settings.SITH_GROUP_PUBLIC_ID])
            p.save(force_lock=True)
            p = Page(name="Services")
            p.save(force_lock=True)
            p.view_groups.set([settings.SITH_GROUP_PUBLIC_ID])
            p.save(force_lock=True)
            PageRev(
                page=p,
                title="Services",
                author=skia,
                content="""
|   |   |   |
| :---: | :---: | :---: |
| [Eboutic](/eboutic) | [Laverie](/launderette) | Matmat |
| SAS | Weekmail | Forum|

""",
            ).save()

            # Subscription
            default_subscription = "un-semestre"
            # Root
            s = Subscription(
                member=User.objects.filter(pk=root.pk).first(),
                subscription_type=default_subscription,
                payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0][0],
            )
            s.subscription_start = s.compute_start()
            s.subscription_end = s.compute_end(
                duration=settings.SITH_SUBSCRIPTIONS[s.subscription_type]["duration"],
                start=s.subscription_start,
            )
            s.save()
            # Skia
            s = Subscription(
                member=User.objects.filter(pk=skia.pk).first(),
                subscription_type=default_subscription,
                payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0][0],
            )
            s.subscription_start = s.compute_start()
            s.subscription_end = s.compute_end(
                duration=settings.SITH_SUBSCRIPTIONS[s.subscription_type]["duration"],
                start=s.subscription_start,
            )
            s.save()
            # Counter admin
            s = Subscription(
                member=User.objects.filter(pk=counter.pk).first(),
                subscription_type=default_subscription,
                payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0][0],
            )
            s.subscription_start = s.compute_start()
            s.subscription_end = s.compute_end(
                duration=settings.SITH_SUBSCRIPTIONS[s.subscription_type]["duration"],
                start=s.subscription_start,
            )
            s.save()
            # Comptable
            s = Subscription(
                member=User.objects.filter(pk=comptable.pk).first(),
                subscription_type=default_subscription,
                payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0][0],
            )
            s.subscription_start = s.compute_start()
            s.subscription_end = s.compute_end(
                duration=settings.SITH_SUBSCRIPTIONS[s.subscription_type]["duration"],
                start=s.subscription_start,
            )
            s.save()
            # Richard
            s = Subscription(
                member=User.objects.filter(pk=r.pk).first(),
                subscription_type=default_subscription,
                payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0][0],
            )
            s.subscription_start = s.compute_start()
            s.subscription_end = s.compute_end(
                duration=settings.SITH_SUBSCRIPTIONS[s.subscription_type]["duration"],
                start=s.subscription_start,
            )
            s.save()
            # User
            s = Subscription(
                member=User.objects.filter(pk=subscriber.pk).first(),
                subscription_type=default_subscription,
                payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0][0],
            )
            s.subscription_start = s.compute_start()
            s.subscription_end = s.compute_end(
                duration=settings.SITH_SUBSCRIPTIONS[s.subscription_type]["duration"],
                start=s.subscription_start,
            )
            s.save()
            # Old subscriber
            s = Subscription(
                member=User.objects.filter(pk=old_subscriber.pk).first(),
                subscription_type=default_subscription,
                payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0][0],
            )
            s.subscription_start = s.compute_start(datetime(year=2012, month=9, day=4))
            s.subscription_end = s.compute_end(
                duration=settings.SITH_SUBSCRIPTIONS[s.subscription_type]["duration"],
                start=s.subscription_start,
            )
            s.save()

            # Clubs
            Club(
                name="Bibo'UT",
                unix_name="bibout",
                address="46 de la Boustifaille",
                parent=main_club,
            ).save()
            guyut = Club(
                name="Guy'UT",
                unix_name="guyut",
                address="42 de la Boustifaille",
                parent=main_club,
            )
            guyut.save()
            Club(
                name="Woenzel'UT", unix_name="woenzel", address="Woenzel", parent=guyut
            ).save()
            Membership(user=skia, club=main_club, role=3, description="").save()
            troll = Club(
                name="Troll Penché",
                unix_name="troll",
                address="Terre Du Milieu",
                parent=main_club,
            )
            troll.save()
            refound = Club(
                name="Carte AE",
                unix_name="carte_ae",
                address="Jamais imprimée",
                parent=main_club,
            )
            refound.save()

            # Counters
            subscribers = Group.objects.get(name="Subscribers")
            old_subscribers = Group.objects.get(name="Old subscribers")
            Customer(user=skia, account_id="6568j", amount=0).save()
            Customer(user=r, account_id="4000k", amount=0).save()
            p = ProductType(name="Bières bouteilles")
            p.save()
            c = ProductType(name="Cotisations")
            c.save()
            r = ProductType(name="Rechargements")
            r.save()
            verre = ProductType(name="Verre")
            verre.save()
            cotis = Product(
                name="Cotis 1 semestre",
                code="1SCOTIZ",
                product_type=c,
                purchase_price="15",
                selling_price="15",
                special_selling_price="15",
                club=main_club,
            )
            cotis.save()
            cotis.buying_groups.add(subscribers)
            cotis.buying_groups.add(old_subscribers)
            cotis.save()
            cotis2 = Product(
                name="Cotis 2 semestres",
                code="2SCOTIZ",
                product_type=c,
                purchase_price="28",
                selling_price="28",
                special_selling_price="28",
                club=main_club,
            )
            cotis2.save()
            cotis2.buying_groups.add(subscribers)
            cotis2.buying_groups.add(old_subscribers)
            cotis2.save()
            refill = Product(
                name="Rechargement 15 €",
                code="15REFILL",
                product_type=r,
                purchase_price="15",
                selling_price="15",
                special_selling_price="15",
                club=main_club,
            )
            refill.save()
            refill.buying_groups.add(subscribers)
            refill.save()
            barb = Product(
                name="Barbar",
                code="BARB",
                product_type=p,
                purchase_price="1.50",
                selling_price="1.7",
                special_selling_price="1.6",
                club=main_club,
                limit_age=18,
            )
            barb.save()
            barb.buying_groups.add(subscribers)
            barb.save()
            cble = Product(
                name="Chimay Bleue",
                code="CBLE",
                product_type=p,
                purchase_price="1.50",
                selling_price="1.7",
                special_selling_price="1.6",
                club=main_club,
                limit_age=18,
            )
            cble.save()
            cble.buying_groups.add(subscribers)
            cble.save()
            cons = Product(
                name="Consigne Eco-cup",
                code="CONS",
                product_type=verre,
                purchase_price="1",
                selling_price="1",
                special_selling_price="1",
                club=main_club,
            )
            cons.save()
            dcons = Product(
                name="Déconsigne Eco-cup",
                code="DECO",
                product_type=verre,
                purchase_price="-1",
                selling_price="-1",
                special_selling_price="-1",
                club=main_club,
            )
            dcons.save()
            cors = Product(
                name="Corsendonk",
                code="CORS",
                product_type=p,
                purchase_price="1.50",
                selling_price="1.7",
                special_selling_price="1.6",
                club=main_club,
                limit_age=18,
            )
            cors.save()
            cors.buying_groups.add(subscribers)
            cors.save()
            carolus = Product(
                name="Carolus",
                code="CARO",
                product_type=p,
                purchase_price="1.50",
                selling_price="1.7",
                special_selling_price="1.6",
                club=main_club,
                limit_age=18,
            )
            carolus.save()
            carolus.buying_groups.add(subscribers)
            carolus.save()
            mde = Counter.objects.filter(name="MDE").first()
            mde.products.add(barb)
            mde.products.add(cble)
            mde.products.add(cons)
            mde.products.add(dcons)
            mde.sellers.add(skia)

            mde.save()

            eboutic = Counter.objects.filter(name="Eboutic").first()
            eboutic.products.add(barb)
            eboutic.products.add(cotis)
            eboutic.products.add(cotis2)
            eboutic.products.add(refill)
            eboutic.save()

            refound_counter = Counter(name="Carte AE", club=refound, type="OFFICE")
            refound_counter.save()
            refound_product = Product(
                name="remboursement",
                code="REMBOURS",
                purchase_price="0",
                selling_price="0",
                special_selling_price="0",
                club=refound,
            )
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
            credit = AccountingType(
                code="74", label="Subventions d'exploitation", movement_type="CREDIT"
            )
            credit.save()
            debit = AccountingType(
                code="606",
                label="Achats non stockés de matières et fournitures(*1)",
                movement_type="DEBIT",
            )
            debit.save()
            debit2 = AccountingType(
                code="604",
                label="Achats d'études et prestations de services(*2)",
                movement_type="DEBIT",
            )
            debit2.save()
            buying = AccountingType(
                code="60", label="Achats (sauf 603)", movement_type="DEBIT"
            )
            buying.save()
            comptes = AccountingType(
                code="6", label="Comptes de charge", movement_type="DEBIT"
            )
            comptes.save()
            simple = SimplifiedAccountingType(
                label="Je fais du simple 6", accounting_type=comptes
            )
            simple.save()
            woenzco = Company(name="Woenzel & co")
            woenzco.save()

            operation_list = [
                (
                    27,
                    "J'avais trop de bière",
                    "CASH",
                    None,
                    buying,
                    "USER",
                    skia.id,
                    "",
                    None,
                ),
                (
                    4000,
                    "Ceci n'est pas une opération... en fait si mais non",
                    "CHECK",
                    None,
                    debit,
                    "COMPANY",
                    woenzco.id,
                    "",
                    23,
                ),
                (
                    22,
                    "C'est de l'argent ?",
                    "CARD",
                    None,
                    credit,
                    "CLUB",
                    troll.id,
                    "",
                    None,
                ),
                (
                    37,
                    "Je paye CASH",
                    "CASH",
                    None,
                    debit2,
                    "OTHER",
                    None,
                    "tous les étudiants <3",
                    None,
                ),
                (300, "Paiement Guy", "CASH", None, buying, "USER", skia.id, "", None),
                (32.3, "Essence", "CASH", None, buying, "OTHER", None, "station", None),
                (
                    46.42,
                    "Allumette",
                    "CHECK",
                    None,
                    credit,
                    "CLUB",
                    main_club.id,
                    "",
                    57,
                ),
                (
                    666.42,
                    "Subvention de far far away",
                    "CASH",
                    None,
                    comptes,
                    "CLUB",
                    main_club.id,
                    "",
                    None,
                ),
                (
                    496,
                    "Ça, c'est un 6",
                    "CARD",
                    simple,
                    None,
                    "USER",
                    skia.id,
                    "",
                    None,
                ),
                (
                    17,
                    "La Gargotte du Korrigan",
                    "CASH",
                    None,
                    debit2,
                    "CLUB",
                    bar_club.id,
                    "",
                    None,
                ),
            ]
            for op in operation_list:
                operation = Operation(
                    journal=gj,
                    date=date.today(),
                    amount=op[0],
                    remark=op[1],
                    mode=op[2],
                    done=True,
                    simpleaccounting_type=op[3],
                    accounting_type=op[4],
                    target_type=op[5],
                    target_id=op[6],
                    target_label=op[7],
                    cheque_number=op[8],
                )
                operation.clean()
                operation.save()

            # Adding user sli
            sli = User(
                username="sli",
                last_name="Li",
                first_name="S",
                email="sli@git.an",
                date_of_birth="1942-06-12",
            )
            sli.set_password("plop")
            sli.save()
            sli.view_groups = [
                Group.objects.filter(name=settings.SITH_MAIN_MEMBERS_GROUP).first().id
            ]
            sli.save()
            sli_profile_path = os.path.join(root_path, "core/fixtures/images/5.jpg")
            with open(sli_profile_path, "rb") as f:
                name = str(sli.id) + "_profile.jpg"
                sli_profile = SithFile(
                    parent=profiles_root,
                    name=name,
                    file=resize_image(Image.open(BytesIO(f.read())), 400, "JPEG"),
                    owner=sli,
                    is_folder=False,
                    mime_type="image/jpeg",
                    size=os.path.getsize(sli_profile_path),
                )
                sli_profile.file.name = name
                sli_profile.save()
                sli.profile_pict = sli_profile
                sli.save()
            # Adding user Krophil
            krophil = User(
                username="krophil",
                last_name="Phil'",
                first_name="Kro",
                email="krophil@git.an",
                date_of_birth="1942-06-12",
            )
            krophil.set_password("plop")
            krophil.save()
            krophil_profile_path = os.path.join(root_path, "core/fixtures/images/6.jpg")
            with open(krophil_profile_path, "rb") as f:
                name = str(krophil.id) + "_profile.jpg"
                krophil_profile = SithFile(
                    parent=profiles_root,
                    name=name,
                    file=resize_image(Image.open(BytesIO(f.read())), 400, "JPEG"),
                    owner=krophil,
                    is_folder=False,
                    mime_type="image/jpeg",
                    size=os.path.getsize(krophil_profile_path),
                )
                krophil_profile.file.name = name
                krophil_profile.save()
                krophil.profile_pict = krophil_profile
                krophil.save()
            # Adding user Com Unity
            comunity = User(
                username="comunity",
                last_name="Unity",
                first_name="Com",
                email="comunity@git.an",
                date_of_birth="1942-06-12",
            )
            comunity.set_password("plop")
            comunity.save()
            comunity.groups.set(
                [Group.objects.filter(name="Communication admin").first().id]
            )
            comunity.save()
            Membership(
                user=comunity,
                club=bar_club,
                start_date=timezone.now(),
                role=settings.SITH_CLUB_ROLES_ID["Board member"],
            ).save()
            # Adding user tutu
            tutu = User(
                username="tutu",
                last_name="Tu",
                first_name="Tu",
                email="tutu@git.an",
                date_of_birth="1942-06-12",
            )
            tutu.set_password("plop")
            tutu.save()
            tutu.groups.set([settings.SITH_GROUP_PEDAGOGY_ADMIN_ID])
            tutu.save()

            # Adding subscription for sli
            s = Subscription(
                member=User.objects.filter(pk=sli.pk).first(),
                subscription_type=list(settings.SITH_SUBSCRIPTIONS.keys())[0],
                payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0][0],
            )
            s.subscription_start = s.compute_start()
            s.subscription_end = s.compute_end(
                duration=settings.SITH_SUBSCRIPTIONS[s.subscription_type]["duration"],
                start=s.subscription_start,
            )
            s.save()
            StudentCard(uid="9A89B82018B0A0", customer=sli.customer).save()
            # Adding subscription for Krophil
            s = Subscription(
                member=User.objects.filter(pk=krophil.pk).first(),
                subscription_type=list(settings.SITH_SUBSCRIPTIONS.keys())[0],
                payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0][0],
            )
            s.subscription_start = s.compute_start()
            s.subscription_end = s.compute_end(
                duration=settings.SITH_SUBSCRIPTIONS[s.subscription_type]["duration"],
                start=s.subscription_start,
            )
            s.save()
            # Com Unity
            s = Subscription(
                member=comunity,
                subscription_type=default_subscription,
                payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0][0],
            )
            s.subscription_start = s.compute_start()
            s.subscription_end = s.compute_end(
                duration=settings.SITH_SUBSCRIPTIONS[s.subscription_type]["duration"],
                start=s.subscription_start,
            )
            s.save()
            # Tutu
            s = Subscription(
                member=tutu,
                subscription_type=default_subscription,
                payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[0][0],
            )
            s.subscription_start = s.compute_start()
            s.subscription_end = s.compute_end(
                duration=settings.SITH_SUBSCRIPTIONS[s.subscription_type]["duration"],
                start=s.subscription_start,
            )
            s.save()

            Selling(
                label=dcons.name,
                product=dcons,
                counter=mde,
                unit_price=dcons.selling_price,
                club=main_club,
                quantity=settings.SITH_ECOCUP_LIMIT + 3,
                seller=skia,
                customer=krophil.customer,
            ).save()

            # Add barman to counter
            c = Counter.objects.get(id=2)
            c.sellers.add(User.objects.get(pk=krophil.pk))
            mde.sellers.add(sli)
            c.save()

            # Create an election
            public_group = Group.objects.get(id=settings.SITH_GROUP_PUBLIC_ID)
            subscriber_group = Group.objects.get(name=settings.SITH_MAIN_MEMBERS_GROUP)
            ae_board_group = Group.objects.get(name=settings.SITH_MAIN_BOARD_GROUP)
            el = Election(
                title="Élection 2017",
                description="La roue tourne",
                start_candidature="1942-06-12 10:28:45+01",
                end_candidature="2042-06-12 10:28:45+01",
                start_date="1942-06-12 10:28:45+01",
                end_date="7942-06-12 10:28:45+01",
            )
            el.save()
            el.view_groups.add(public_group)
            el.edit_groups.add(ae_board_group)
            el.candidature_groups.add(subscriber_group)
            el.vote_groups.add(subscriber_group)
            el.save()
            liste = ElectionList(title="Candidature Libre", election=el)
            liste.save()
            listeT = ElectionList(title="Troll", election=el)
            listeT.save()
            pres = Role(election=el, title="Président AE", description="Roi de l'AE")
            pres.save()
            resp = Role(
                election=el, title="Co Respo Info", max_choice=2, description="Ghetto++"
            )
            resp.save()
            cand = Candidature(
                role=resp, user=skia, election_list=liste, program="Refesons le site AE"
            )
            cand.save()
            cand = Candidature(
                role=resp,
                user=sli,
                election_list=liste,
                program="Vasy je deviens mon propre adjoint",
            )
            cand.save()
            cand = Candidature(
                role=resp, user=krophil, election_list=listeT, program="Le Pôle Troll !"
            )
            cand.save()
            cand = Candidature(
                role=pres,
                user=sli,
                election_list=listeT,
                program="En fait j'aime pas l'info, je voulais faire GMC",
            )
            cand.save()

            # Forum
            room = Forum(
                name="Salon de discussions",
                description="Pour causer de tout",
                is_category=True,
            )
            room.save()
            Forum(name="AE", description="Réservé au bureau AE", parent=room).save()
            Forum(name="BdF", description="Réservé au bureau BdF", parent=room).save()
            hall = Forum(
                name="Hall de discussions",
                description="Pour toutes les discussions",
                parent=room,
            )
            hall.save()
            various = Forum(
                name="Divers", description="Pour causer de rien", is_category=True
            )
            various.save()
            Forum(
                name="Promos", description="Réservé aux Promos", parent=various
            ).save()
            ForumTopic(forum=hall)

            # News
            friday = timezone.now()
            while friday.weekday() != 4:
                friday += timedelta(hours=6)
            friday.replace(hour=20, minute=0, second=0)
            # Event
            n = News(
                title="Apero barman",
                summary="Viens boire un coup avec les barmans",
                content="Glou glou glou glou glou glou glou",
                type="EVENT",
                club=bar_club,
                author=subscriber,
                is_moderated=True,
                moderator=skia,
            )
            n.save()
            NewsDate(
                news=n,
                start_date=timezone.now() + timedelta(hours=70),
                end_date=timezone.now() + timedelta(hours=72),
            ).save()
            n = News(
                title="Repas barman",
                summary="Enjoy la fin du semestre!",
                content="Viens donc t'enjailler avec les autres barmans aux "
                "frais du BdF! \o/",
                type="EVENT",
                club=bar_club,
                author=subscriber,
                is_moderated=True,
                moderator=skia,
            )
            n.save()
            NewsDate(
                news=n,
                start_date=timezone.now() + timedelta(hours=72),
                end_date=timezone.now() + timedelta(hours=84),
            ).save()
            n = News(
                title="Repas fromager",
                summary="Wien manger du l'bon fromeug'",
                content="Fô viendre mangey d'la bonne fondue!",
                type="EVENT",
                club=bar_club,
                author=subscriber,
                is_moderated=True,
                moderator=skia,
            )
            n.save()
            NewsDate(
                news=n,
                start_date=timezone.now() + timedelta(hours=96),
                end_date=timezone.now() + timedelta(hours=100),
            ).save()
            n = News(
                title="SdF",
                summary="Enjoy la fin des finaux!",
                content="Viens faire la fête avec tout plein de gens!",
                type="EVENT",
                club=bar_club,
                author=subscriber,
                is_moderated=True,
                moderator=skia,
            )
            n.save()
            NewsDate(
                news=n,
                start_date=friday + timedelta(hours=24 * 7 + 1),
                end_date=timezone.now() + timedelta(hours=24 * 7 + 9),
            ).save()
            # Weekly
            n = News(
                title="Jeux sans faim",
                summary="Viens jouer!",
                content="Rejoins la fine équipe du Troll Penché et viens "
                "d'amuser le Vendredi soir!",
                type="WEEKLY",
                club=troll,
                author=subscriber,
                is_moderated=True,
                moderator=skia,
            )
            n.save()
            for i in range(10):
                NewsDate(
                    news=n,
                    start_date=friday + timedelta(hours=24 * 7 * i),
                    end_date=friday + timedelta(hours=24 * 7 * i + 8),
                ).save()

            # Create som data for pedagogy

            UV(
                code="PA00",
                author=User.objects.get(id=0),
                credit_type=settings.SITH_PEDAGOGY_UV_TYPE[3][0],
                manager="Laurent HEYBERGER",
                semester=settings.SITH_PEDAGOGY_UV_SEMESTER[3][0],
                language=settings.SITH_PEDAGOGY_UV_LANGUAGE[0][0],
                department=settings.SITH_PROFILE_DEPARTMENTS[-2][0],
                credits=5,
                title="Participation dans une association étudiante",
                objectives="* Permettre aux étudiants de réaliser, pendant un semestre, un projet culturel ou associatif et de le valoriser.",
                program="""* Semestre précédent proposition d'un projet et d'un cahier des charges
* Evaluation par un jury de six membres
* Si accord réalisation dans le cadre de l'UV
* Compte-rendu de l'expérience
* Présentation""",
                skills="""* Gérer un projet associatif ou une action éducative en autonomie:
* en produisant un cahier des charges qui -définit clairement le contexte du projet personnel -pose les jalons de ce projet -estime de manière réaliste les moyens et objectifs du projet -définit exactement les livrables attendus
    * en étant capable de respecter ce cahier des charges ou, le cas échéant, de réviser le cahier des charges de manière argumentée.
* Relater son expérience dans un rapport:
* qui permettra à d'autres étudiants de poursuivre les actions engagées
* qui montre la capacité à s'auto-évaluer et à adopter une distance critique sur son action.""",
                key_concepts="""* Autonomie
* Responsabilité
* Cahier des charges
* Gestion de projet""",
                hours_THE=121,
                hours_TE=4,
            ).save()
