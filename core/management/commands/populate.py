#
# Copyright 2016,2017,2023
# - Skia <skia@hya.sk>
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
from datetime import date, timedelta
from io import StringIO
from pathlib import Path
from typing import ClassVar, NamedTuple

from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Q
from django.utils import timezone
from django.utils.timezone import localdate
from PIL import Image

from club.models import Club, Membership
from com.ics_calendar import IcsCalendar
from com.models import News, NewsDate, Sith, Weekmail
from core.models import BanGroup, Group, Page, PageRev, SithFile, User
from core.utils import resize_image
from counter.models import Counter, Product, ProductType, ReturnableProduct, StudentCard
from election.models import Candidature, Election, ElectionList, Role
from forum.models import Forum
from pedagogy.models import UE
from sas.models import Album, PeoplePictureRelation, Picture
from subscription.models import Subscription


class PopulatedGroups(NamedTuple):
    root: Group
    public: Group
    subscribers: Group
    old_subscribers: Group
    sas_admin: Group
    com_admin: Group
    counter_admin: Group
    accounting_admin: Group
    pedagogy_admin: Group
    campus_admin: Group


class Command(BaseCommand):
    ROOT_PATH: ClassVar[Path] = Path(__file__).parent.parent.parent.parent
    SAS_FIXTURE_PATH: ClassVar[Path] = (
        ROOT_PATH / "core" / "fixtures" / "images" / "sas"
    )

    help = "Populate a new instance of the Sith AE"

    def reset_index(self, *args):
        if connection.vendor == "sqlite":
            # sqlite doesn't support this operation
            return
        sqlcmd = StringIO()
        call_command("sqlsequencereset", "--no-color", *args, stdout=sqlcmd)
        cursor = connection.cursor()
        cursor.execute(sqlcmd.getvalue())

    def handle(self, *args, **options):
        if not settings.DEBUG and not settings.TESTING:
            raise Exception("Never call this command in prod. Never.")

        Sith.objects.create(weekmail_destinations="etudiants@git.an personnel@git.an")

        site = Site.objects.get_current()
        site.domain = settings.SITH_URL
        site.name = settings.SITH_NAME
        site.save()

        groups = self._create_groups()
        self._create_ban_groups()

        root = User.objects.create_superuser(
            id=0,
            username="root",
            last_name="",
            first_name="Bibou",
            email="ae.info@utbm.fr",
            date_of_birth="1942-06-12",
            password="plop",
        )
        self.profiles_root = SithFile.objects.create(name="profiles", owner=root)
        home_root = SithFile.objects.create(name="users", owner=root)

        # Page needed for club creation
        p = Page(name=settings.SITH_CLUB_ROOT_PAGE)
        p.save(force_lock=True)

        club_root = SithFile.objects.create(name="clubs", owner=root)
        main_club = Club.objects.create(
            id=1, name="AE", address="6 Boulevard Anatole France, 90000 Belfort"
        )
        main_club.board_group.permissions.add(
            *Permission.objects.filter(
                codename__in=["view_subscription", "add_subscription"]
            )
        )
        bar_club = Club.objects.create(
            id=settings.SITH_PDF_CLUB_ID,
            name="PdF",
            address="6 Boulevard Anatole France, 90000 Belfort",
        )

        self.reset_index("club")
        for bar_id, bar_name in settings.SITH_COUNTER_BARS:
            Counter(id=bar_id, name=bar_name, club=bar_club, type="BAR").save()
        self.reset_index("counter")
        counters = [
            Counter(name="Eboutic", club=main_club, type="EBOUTIC"),
            Counter(name="AE", club=main_club, type="OFFICE"),
            Counter(name="Vidage comptes AE", club=main_club, type="OFFICE"),
        ]
        Counter.objects.bulk_create(counters)
        bar_groups = []
        for bar_id, bar_name in settings.SITH_COUNTER_BARS:
            group = Group.objects.create(
                name=f"{bar_name} admin", is_manually_manageable=True
            )
            bar_groups.append(
                Counter.edit_groups.through(counter_id=bar_id, group=group)
            )
        Counter.edit_groups.through.objects.bulk_create(bar_groups)
        self.reset_index("counter")

        groups.subscribers.viewable_files.add(home_root, club_root)

        Weekmail().save()

        # Here we add a lot of test datas, that are not necessary for the Sith,
        # but that provide a basic development environment
        self.now = timezone.now().replace(hour=12, second=0)

        skia = User.objects.create_user(
            username="skia",
            last_name="Kia",
            first_name="S'",
            email="skia@git.an",
            date_of_birth="1942-06-12",
            password="plop",
        )
        public = User.objects.create_user(
            username="public",
            last_name="Not subscribed",
            first_name="Public",
            email="public@git.an",
            date_of_birth="1942-06-12",
            password="plop",
        )
        subscriber = User.objects.create_user(
            username="subscriber",
            last_name="User",
            first_name="Subscribed",
            email="Subscribed@git.an",
            date_of_birth="1942-06-12",
            password="plop",
        )
        old_subscriber = User.objects.create_user(
            username="old_subscriber",
            last_name="Subscriber",
            first_name="Old",
            email="old_subscriber@git.an",
            date_of_birth="1942-06-12",
            password="plop",
        )
        counter = User.objects.create_user(
            username="counter",
            last_name="Ter",
            first_name="Coun",
            email="counter@git.an",
            date_of_birth="1942-06-12",
            password="plop",
        )
        comptable = User.objects.create_user(
            username="comptable",
            last_name="Able",
            first_name="Compte",
            email="compta@git.an",
            date_of_birth="1942-06-12",
            password="plop",
        )
        User.objects.create_user(
            username="guy",
            last_name="Carlier",
            first_name="Guy",
            email="guy@git.an",
            date_of_birth="1942-06-12",
            password="plop",
        )
        richard = User.objects.create_user(
            username="rbatsbak",
            last_name="Batsbak",
            first_name="Richard",
            email="richard@git.an",
            date_of_birth="1982-06-12",
            password="plop",
        )
        sli = User.objects.create_user(
            username="sli",
            last_name="Li",
            first_name="S",
            email="sli@git.an",
            date_of_birth="1942-06-12",
            password="plop",
        )
        krophil = User.objects.create_user(
            username="krophil",
            last_name="Phil'",
            first_name="Kro",
            email="krophil@git.an",
            date_of_birth="1942-06-12",
            password="plop",
        )
        comunity = User.objects.create_user(
            username="comunity",
            last_name="Unity",
            first_name="Com",
            email="comunity@git.an",
            date_of_birth="1942-06-12",
            password="plop",
        )
        tutu = User.objects.create_user(
            username="tutu",
            last_name="Tu",
            first_name="Tu",
            email="tutu@git.an",
            date_of_birth="1942-06-12",
            password="plop",
        )
        User.groups.through.objects.bulk_create(
            [
                User.groups.through(group=groups.counter_admin, user=counter),
                User.groups.through(group=groups.accounting_admin, user=comptable),
                User.groups.through(group=groups.com_admin, user=comunity),
                User.groups.through(group=groups.pedagogy_admin, user=tutu),
                User.groups.through(group=groups.sas_admin, user=skia),
            ]
        )
        for user in richard, sli, krophil, skia:
            self._create_profile_pict(user)

        User.godfathers.through.objects.bulk_create(
            [
                User.godfathers.through(from_user=richard, to_user=comptable),
                User.godfathers.through(from_user=root, to_user=skia),
                User.godfathers.through(from_user=skia, to_user=root),
                User.godfathers.through(from_user=sli, to_user=skia),
                User.godfathers.through(from_user=public, to_user=richard),
                User.godfathers.through(from_user=subscriber, to_user=richard),
            ]
        )

        # Adding syntax help page
        syntax_page = Page(name="Aide_sur_la_syntaxe")
        syntax_page.save(force_lock=True)
        PageRev.objects.create(
            page=syntax_page,
            title="Aide sur la syntaxe",
            author=skia,
            content=(self.ROOT_PATH / "core" / "fixtures" / "SYNTAX.md").read_text(),
        )
        services_page = Page(name="Services")
        services_page.save(force_lock=True)
        PageRev.objects.create(
            page=services_page,
            title="Services",
            author=skia,
            content="- [Eboutic](/eboutic)\n- Matmat\n- SAS\n- Weekmail\n- Forum",
        )

        index_page = Page(name="Index")
        index_page.save(force_lock=True)
        PageRev.objects.create(
            page=index_page,
            title="Wiki index",
            author=root,
            content="Welcome to the wiki page!",
        )

        groups.public.viewable_page.set([syntax_page, services_page, index_page])

        self._create_subscription(root)
        self._create_subscription(skia)
        self._create_subscription(counter)
        self._create_subscription(comptable)
        self._create_subscription(richard)
        self._create_subscription(subscriber)
        self._create_subscription(old_subscriber, start=date(year=2012, month=9, day=4))
        self._create_subscription(sli)
        self._create_subscription(krophil)
        self._create_subscription(comunity)
        self._create_subscription(tutu)
        StudentCard(uid="9A89B82018B0A0", customer=sli.customer).save()

        # Clubs
        Club.objects.create(
            name="Bibo'UT", address="46 de la Boustifaille", parent=main_club
        )
        guyut = Club.objects.create(
            name="Guy'UT", address="42 de la Boustifaille", parent=main_club
        )
        Club.objects.create(name="Woenzel'UT", address="Woenzel", parent=guyut)
        troll = Club.objects.create(
            name="Troll Penché", address="Terre Du Milieu", parent=main_club
        )
        refound = Club.objects.create(
            name="Carte AE", address="Jamais imprimée", parent=main_club
        )

        Membership.objects.create(user=skia, club=main_club, role=3)
        Membership.objects.create(
            user=comunity,
            club=bar_club,
            start_date=localdate(),
            role=settings.SITH_CLUB_ROLES_ID["Board member"],
        )
        Membership.objects.create(
            user=sli,
            club=troll,
            role=9,
            description="Padawan Troll",
            start_date=localdate() - timedelta(days=17),
        )
        Membership.objects.create(
            user=krophil,
            club=troll,
            role=10,
            description="Maitre Troll",
            start_date=localdate() - timedelta(days=200),
        )
        Membership.objects.create(
            user=skia,
            club=troll,
            role=2,
            description="Grand Ancien Troll",
            start_date=localdate() - timedelta(days=400),
            end_date=localdate() - timedelta(days=86),
        )
        Membership.objects.create(
            user=richard,
            club=troll,
            role=2,
            description="",
            start_date=localdate() - timedelta(days=200),
            end_date=localdate() - timedelta(days=100),
        )

        p = ProductType.objects.create(name="Bières bouteilles")
        c = ProductType.objects.create(name="Cotisations")
        r = ProductType.objects.create(name="Rechargements")
        verre = ProductType.objects.create(name="Verre")
        cotis = Product.objects.create(
            name="Cotis 1 semestre",
            code="1SCOTIZ",
            product_type=c,
            purchase_price="15",
            selling_price="15",
            special_selling_price="15",
            club=main_club,
        )
        cotis2 = Product.objects.create(
            name="Cotis 2 semestres",
            code="2SCOTIZ",
            product_type=c,
            purchase_price="28",
            selling_price="28",
            special_selling_price="28",
            club=main_club,
        )
        refill = Product.objects.create(
            name="Rechargement 15 €",
            code="15REFILL",
            product_type=r,
            purchase_price="15",
            selling_price="15",
            special_selling_price="15",
            club=main_club,
        )
        barb = Product.objects.create(
            name="Barbar",
            code="BARB",
            product_type=p,
            purchase_price="1.50",
            selling_price="1.7",
            special_selling_price="1.6",
            club=main_club,
            limit_age=18,
        )
        cble = Product.objects.create(
            name="Chimay Bleue",
            code="CBLE",
            product_type=p,
            purchase_price="1.50",
            selling_price="1.7",
            special_selling_price="1.6",
            club=main_club,
            limit_age=18,
        )
        cons = Product.objects.create(
            name="Consigne Eco-cup",
            code="CONS",
            product_type=verre,
            purchase_price="1",
            selling_price="1",
            special_selling_price="1",
            club=main_club,
        )
        dcons = Product.objects.create(
            name="Déconsigne Eco-cup",
            code="DECO",
            product_type=verre,
            purchase_price="-1",
            selling_price="-1",
            special_selling_price="-1",
            club=main_club,
        )
        cors = Product.objects.create(
            name="Corsendonk",
            code="CORS",
            product_type=p,
            purchase_price="1.50",
            selling_price="1.7",
            special_selling_price="1.6",
            club=main_club,
            limit_age=18,
        )
        carolus = Product.objects.create(
            name="Carolus",
            code="CARO",
            product_type=p,
            purchase_price="1.50",
            selling_price="1.7",
            special_selling_price="1.6",
            club=main_club,
            limit_age=18,
        )
        Product.objects.create(
            name="remboursement",
            code="REMBOURS",
            purchase_price="0",
            selling_price="0",
            special_selling_price="0",
            club=refound,
        )
        groups.subscribers.products.add(
            cotis, cotis2, refill, barb, cble, cors, carolus
        )
        groups.old_subscribers.products.add(cotis, cotis2)

        mde = Counter.objects.get(name="MDE")
        mde.products.add(barb, cble, cons, dcons)

        eboutic = Counter.objects.get(name="Eboutic")
        eboutic.products.add(barb, cotis, cotis2, refill)

        Counter.objects.create(name="Carte AE", club=refound, type="OFFICE")

        ReturnableProduct.objects.create(
            product=cons, returned_product=dcons, max_return=3
        )

        # Add barman to counter
        Counter.sellers.through.objects.bulk_create(
            [
                Counter.sellers.through(counter_id=2, user=krophil),
                Counter.sellers.through(counter=mde, user=skia),
            ]
        )

        # Create an election
        el = Election.objects.create(
            title="Élection 2017",
            description="La roue tourne",
            start_candidature="1942-06-12 10:28:45+01",
            end_candidature="2042-06-12 10:28:45+01",
            start_date="1942-06-12 10:28:45+01",
            end_date="7942-06-12 10:28:45+01",
        )
        el.view_groups.add(groups.public)
        el.edit_groups.add(main_club.board_group)
        el.candidature_groups.add(groups.subscribers)
        el.vote_groups.add(groups.subscribers)
        liste = ElectionList.objects.create(title="Candidature Libre", election=el)
        listeT = ElectionList.objects.create(title="Troll", election=el)
        pres = Role.objects.create(
            election=el, title="Président AE", description="Roi de l'AE"
        )
        resp = Role.objects.create(
            election=el, title="Co Respo Info", max_choice=2, description="Ghetto++"
        )
        Candidature.objects.bulk_create(
            [
                Candidature(
                    role=resp,
                    user=skia,
                    election_list=liste,
                    program="Refesons le site AE",
                ),
                Candidature(
                    role=resp,
                    user=sli,
                    election_list=liste,
                    program="Vasy je deviens mon propre adjoint",
                ),
                Candidature(
                    role=resp,
                    user=krophil,
                    election_list=listeT,
                    program="Le Pôle Troll !",
                ),
                Candidature(
                    role=pres,
                    user=sli,
                    election_list=listeT,
                    program="En fait j'aime pas l'info, je voulais faire GMC",
                ),
            ]
        )

        # Forum
        room = Forum.objects.create(
            name="Salon de discussions",
            description="Pour causer de tout",
            is_category=True,
        )
        various = Forum.objects.create(
            name="Divers", description="Pour causer de rien", is_category=True
        )
        Forum.objects.bulk_create(
            [
                Forum(name="AE", description="Réservé au bureau AE", parent=room),
                Forum(name="BdF", description="Réservé au bureau BdF", parent=room),
                Forum(name="Promos", description="Réservé aux Promos", parent=various),
                Forum(
                    name="Hall de discussions",
                    description="Pour toutes les discussions",
                    parent=room,
                ),
            ]
        )

        # News
        friday = self.now
        while friday.weekday() != 4:
            friday += timedelta(hours=6)
        friday.replace(hour=20, minute=0)
        # Event
        news_dates = []
        n = News.objects.create(
            title="Apero barman",
            summary="Viens boire un coup avec les barmans",
            content="Glou glou glou glou glou glou glou",
            club=bar_club,
            author=subscriber,
            is_published=True,
            moderator=skia,
        )
        news_dates.append(
            NewsDate(
                news=n,
                start_date=self.now + timedelta(hours=70),
                end_date=self.now + timedelta(hours=72),
            )
        )
        n = News.objects.create(
            title="Repas barman",
            summary="Enjoy la fin du semestre!",
            content=(
                "Viens donc t'enjailler avec les autres barmans aux frais du BdF! \\o/"
            ),
            club=bar_club,
            author=subscriber,
            is_published=True,
            moderator=skia,
        )
        news_dates.append(
            NewsDate(
                news=n,
                start_date=self.now + timedelta(hours=72),
                end_date=self.now + timedelta(hours=84),
            )
        )
        News.objects.create(
            title="Repas fromager",
            summary="Wien manger du l'bon fromeug'",
            content="Fô viendre mangey d'la bonne fondue!",
            club=bar_club,
            author=subscriber,
            is_published=True,
            moderator=skia,
        )
        news_dates.append(
            NewsDate(
                news=n,
                start_date=self.now + timedelta(hours=96),
                end_date=self.now + timedelta(hours=100),
            )
        )
        n = News.objects.create(
            title="SdF",
            summary="Enjoy la fin des finaux!",
            content="Viens faire la fête avec tout plein de gens!",
            club=bar_club,
            author=subscriber,
            is_published=True,
            moderator=skia,
        )
        news_dates.append(
            NewsDate(
                news=n,
                start_date=friday + timedelta(hours=24 * 7 + 1),
                end_date=friday + timedelta(hours=24 * 7 + 9),
            )
        )
        # Weekly
        n = News.objects.create(
            title="Jeux sans faim",
            summary="Viens jouer!",
            content="Rejoins la fine équipe du Troll Penché et viens "
            "t'amuser le Vendredi soir!",
            club=troll,
            author=subscriber,
            is_published=True,
            moderator=skia,
        )
        news_dates.extend(
            [
                NewsDate(
                    news=n,
                    start_date=friday + timedelta(days=7 * i),
                    end_date=friday + timedelta(days=7 * i, hours=8),
                )
                for i in range(10)
            ]
        )
        NewsDate.objects.bulk_create(news_dates)
        IcsCalendar.make_internal()  # Force refresh of the calendar after a bulk_create

        # Create some data for pedagogy

        UE(
            code="PA00",
            author=User.objects.get(id=0),
            credit_type=settings.SITH_PEDAGOGY_UE_TYPE[3][0],
            manager="Laurent HEYBERGER",
            semester=settings.SITH_PEDAGOGY_UE_SEMESTER[3][0],
            language=settings.SITH_PEDAGOGY_UE_LANGUAGE[0][0],
            department=settings.SITH_PROFILE_DEPARTMENTS[-2][0],
            credits=5,
            title="Participation dans une association étudiante",
            objectives="* Permettre aux étudiants de réaliser, pendant un semestre, un projet culturel ou associatif et de le valoriser.",
            program="""* Semestre précédent proposition d'un projet et d'un cahier des charges
* Evaluation par un jury de six membres
* Si accord réalisation dans le cadre de l'UE
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

        # SAS
        for f in self.SAS_FIXTURE_PATH.glob("*"):
            if f.is_dir():
                album = Album.objects.create(name=f.name, is_moderated=True)
                for p in f.iterdir():
                    file = resize_image(Image.open(p), 1000, "WEBP")
                    pict = Picture(
                        parent=album,
                        name=p.name,
                        original=file,
                        owner=root,
                        is_moderated=True,
                    )
                    pict.original.name = pict.name
                    pict.generate_thumbnails()
                    pict.full_clean()
                    pict.save()
                album.generate_thumbnail()

        img_skia = Picture.objects.get(name="skia.jpg")
        img_sli = Picture.objects.get(name="sli.jpg")
        img_krophil = Picture.objects.get(name="krophil.jpg")
        img_skia_sli = Picture.objects.get(name="skia_sli.jpg")
        img_skia_sli_krophil = Picture.objects.get(name="skia_sli_krophil.jpg")
        img_richard = Picture.objects.get(name="rbatsbak.jpg")
        PeoplePictureRelation.objects.bulk_create(
            [
                PeoplePictureRelation(user=skia, picture=img_skia),
                PeoplePictureRelation(user=sli, picture=img_sli),
                PeoplePictureRelation(user=krophil, picture=img_krophil),
                PeoplePictureRelation(user=skia, picture=img_skia_sli),
                PeoplePictureRelation(user=sli, picture=img_skia_sli),
                PeoplePictureRelation(user=skia, picture=img_skia_sli_krophil),
                PeoplePictureRelation(user=sli, picture=img_skia_sli_krophil),
                PeoplePictureRelation(user=krophil, picture=img_skia_sli_krophil),
                PeoplePictureRelation(user=richard, picture=img_richard),
            ]
        )

    def _create_profile_pict(self, user: User):
        path = self.SAS_FIXTURE_PATH / "Family" / f"{user.username}.jpg"
        file = resize_image(Image.open(path), 400, "WEBP")
        name = f"{user.id}_profile.webp"
        profile = SithFile(
            parent=self.profiles_root,
            name=name,
            file=file,
            owner=user,
            is_folder=False,
            mime_type="image/webp",
            size=file.size,
        )
        profile.file.name = name
        profile.save()
        user.profile_pict = profile
        user.save()

    def _create_subscription(
        self,
        user: User,
        subscription_type: str = "un-semestre",
        start: date | None = None,
    ):
        s = Subscription(
            member=user,
            subscription_type=subscription_type,
            payment_method=settings.SITH_SUBSCRIPTION_PAYMENT_METHOD[1][0],
        )
        s.subscription_start = s.compute_start(start)
        s.subscription_end = s.compute_end(
            duration=settings.SITH_SUBSCRIPTIONS[s.subscription_type]["duration"],
            start=s.subscription_start,
        )
        s.save()

    def _create_groups(self) -> PopulatedGroups:
        perms = Permission.objects.all()

        root_group = Group.objects.create(name="Root", is_manually_manageable=True)
        root_group.permissions.add(*list(perms.values_list("pk", flat=True)))
        # public has no permission.
        # Its purpose is not to link users to permissions,
        # but to other objects (like products)
        public_group = Group.objects.create(name="Publique")

        subscribers = Group.objects.create(name="Cotisants")
        subscribers.permissions.add(
            *list(perms.filter(codename__in=["add_news", "add_uecomment"]))
        )
        old_subscribers = Group.objects.create(name="Anciens cotisants")
        old_subscribers.permissions.add(
            *list(
                perms.filter(
                    codename__in=[
                        "view_ue",
                        "view_uecomment",
                        "add_uecommentreport",
                        "view_user",
                        "view_picture",
                        "view_album",
                        "view_peoplepicturerelation",
                        "add_peoplepicturerelation",
                        "add_page",
                        "add_quickuploadimage",
                        "view_club",
                        "access_lookup",
                    ]
                )
            )
        )
        accounting_admin = Group.objects.create(
            name="Admin comptabilité", is_manually_manageable=True
        )
        accounting_admin.permissions.add(
            *list(
                perms.filter(
                    Q(
                        codename__in=[
                            "view_customer",
                            "view_product",
                            "change_product",
                            "add_product",
                            "view_producttype",
                            "change_producttype",
                            "add_producttype",
                            "delete_selling",
                        ]
                    )
                ).values_list("pk", flat=True)
            )
        )
        com_admin = Group.objects.create(
            name="Admin communication", is_manually_manageable=True
        )
        com_admin.permissions.add(
            *list(
                perms.filter(content_type__app_label="com").values_list("pk", flat=True)
            )
        )
        counter_admin = Group.objects.create(
            name="Admin comptoirs", is_manually_manageable=True
        )
        counter_admin.permissions.add(
            *list(
                perms.filter(
                    Q(content_type__app_label__in=["counter"])
                    & ~Q(codename__in=["delete_product", "delete_producttype"])
                )
            )
        )
        sas_admin = Group.objects.create(name="Admin SAS", is_manually_manageable=True)
        sas_admin.permissions.add(
            *list(
                perms.filter(content_type__app_label="sas").values_list("pk", flat=True)
            )
        )
        forum_admin = Group.objects.create(
            name="Admin forum", is_manually_manageable=True
        )
        forum_admin.permissions.add(
            *list(
                perms.filter(content_type__app_label="forum").values_list(
                    "pk", flat=True
                )
            )
        )
        pedagogy_admin = Group.objects.create(
            name="Admin pédagogie", is_manually_manageable=True
        )
        pedagogy_admin.permissions.add(
            *list(
                perms.filter(content_type__app_label="pedagogy")
                .exclude(codename__in=["change_uecomment"])
                .values_list("pk", flat=True)
            )
        )
        campus_admin = Group.objects.create(
            name="Respo site", is_manually_manageable=True
        )
        campus_admin.permissions.add(
            *counter_admin.permissions.values_list("pk", flat=True),
            *perms.filter(content_type__app_label="reservation").values_list(
                "pk", flat=True
            ),
        )

        self.reset_index("core", "auth")

        return PopulatedGroups(
            root=root_group,
            public=public_group,
            subscribers=subscribers,
            old_subscribers=old_subscribers,
            com_admin=com_admin,
            counter_admin=counter_admin,
            accounting_admin=accounting_admin,
            sas_admin=sas_admin,
            pedagogy_admin=pedagogy_admin,
            campus_admin=campus_admin,
        )

    def _create_ban_groups(self):
        BanGroup.objects.create(name="Banned from buying alcohol", description="")
        BanGroup.objects.create(name="Banned from counters", description="")
        BanGroup.objects.create(name="Banned to subscribe", description="")
