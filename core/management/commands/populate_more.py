import math
import random
from datetime import date, timedelta
from datetime import timezone as tz
from typing import Iterator

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db.models import Count, Exists, Min, OuterRef, Subquery
from django.utils.timezone import localdate, make_aware, now
from faker import Faker

from club.models import Club, Membership
from core.models import Group, User
from counter.models import (
    Counter,
    Customer,
    Permanency,
    Product,
    ProductType,
    Refilling,
    Selling,
)
from forum.models import Forum, ForumMessage, ForumTopic
from pedagogy.models import UV
from subscription.models import Subscription


class Command(BaseCommand):
    help = "Add more fixtures for a more complete development environment"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.faker = Faker("fr_FR")

    def add_arguments(self, parser):
        parser.add_argument(
            "-n", "--nb-users", help="Number of users to create", type=int, default=600
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise Exception("Never call this command in prod. Never.")

        self.stdout.write("Creating users...")
        users = self.create_users(options["nb_users"])
        subscribers = random.sample(users, k=int(0.8 * len(users)))
        self.stdout.write("Creating subscriptions...")
        self.create_subscriptions(subscribers)
        self.stdout.write("Creating club memberships...")
        users_qs = User.objects.filter(id__in=[s.id for s in subscribers])
        subscribers_now = list(
            users_qs.annotate(
                filter=Exists(
                    Subscription.objects.filter(
                        member_id=OuterRef("pk"), subscription_end__gte=now()
                    )
                )
            )
        )
        old_subscribers = list(
            users_qs.annotate(
                filter=Exists(
                    Subscription.objects.filter(
                        member_id=OuterRef("pk"), subscription_end__lt=now()
                    )
                )
            )
        )
        self.make_club(
            Club.objects.get(id=settings.SITH_MAIN_CLUB_ID),
            random.sample(subscribers_now, k=min(30, len(subscribers_now))),
            random.sample(old_subscribers, k=min(60, len(old_subscribers))),
        )
        self.make_club(
            Club.objects.get(name="Troll Penché"),
            random.sample(subscribers_now, k=min(20, len(subscribers_now))),
            random.sample(old_subscribers, k=min(80, len(old_subscribers))),
        )
        self.stdout.write("Creating uvs...")
        self.create_uvs()
        self.stdout.write("Creating products...")
        self.create_products()
        self.stdout.write("Creating sales and refills...")
        sellers = random.sample(users, len(users) // 10)
        self.create_sales(sellers)
        self.stdout.write("Creating permanences...")
        self.create_permanences(sellers)
        self.stdout.write("Filling the forum...")
        self.create_forums()

        self.stdout.write("Done")

    def create_users(self, nb_users: int = 600) -> list[User]:
        password = make_password("plop")
        users = [
            User(
                username=self.faker.user_name(),
                first_name=self.faker.first_name(),
                last_name=self.faker.last_name(),
                date_of_birth=(
                    None
                    if random.random() < 0.2
                    else self.faker.date_of_birth(minimum_age=15, maximum_age=25)
                ),
                email=self.faker.email(),
                phone=self.faker.phone_number(),
                address=self.faker.address(),
                password=password,
            )
            for _ in range(nb_users)
        ]
        # there may a duplicate or two
        # Not a problem, we will just have 599 users instead of 600
        users = User.objects.bulk_create(users, ignore_conflicts=True)
        users = list(User.objects.order_by("-id")[: len(users)])
        public_group = Group.objects.get(pk=settings.SITH_GROUP_PUBLIC_ID)
        public_group.users.add(*users)
        return users

    def create_subscriptions(self, users: list[User]):
        def prepare_subscription(_user: User, start_date: date) -> Subscription:
            payment_method = random.choice(settings.SITH_SUBSCRIPTION_PAYMENT_METHOD)[0]
            duration = random.randint(1, 4)
            sub = Subscription(member=_user, payment_method=payment_method)
            sub.subscription_start = sub.compute_start(d=start_date, duration=duration)
            sub.subscription_end = sub.compute_end(duration)
            return sub

        subscriptions = []
        customers = []
        # first set of subscriptions
        for i, user in enumerate(users):
            sub = prepare_subscription(user, self.faker.past_date("-10y"))
            subscriptions.append(sub)
            customers.append(
                Customer(
                    user=user,
                    account_id=f"{9900 + i}{self.faker.random_lowercase_letter()}",
                )
            )
            while sub.subscription_end < localdate() and random.random() > 0.7:
                # 70% chances to subscribe again
                # (expect if it would make the subscription start after tomorrow)
                sub = prepare_subscription(
                    user, self.faker.past_date(sub.subscription_end)
                )
                subscriptions.append(sub)
        old_subscriber_group = Group.objects.get(
            pk=settings.SITH_GROUP_OLD_SUBSCRIBERS_ID
        )
        old_subscriber_group.users.add(*users)
        Subscription.objects.bulk_create(subscriptions)
        Customer.objects.bulk_create(customers, ignore_conflicts=True)

    def make_club(self, club: Club, members: list[User], old_members: list[User]):
        def zip_roles(users: list[User]) -> Iterator[tuple[User, int]]:
            roles = iter(sorted(settings.SITH_CLUB_ROLES.keys(), reverse=True))
            user_idx = 0
            while (role := next(roles)) > 2:
                # one member for each major role
                yield users[user_idx], role
                user_idx += 1
            for _ in range(int(0.3 * (len(users) - user_idx))):
                # 30% of the remaining in the board
                yield users[user_idx], 2
                user_idx += 1
            for remaining in users[user_idx + 1 :]:
                # everything else is a simple member
                yield remaining, 1

        memberships = []
        old_members = old_members.copy()
        random.shuffle(old_members)
        for old in old_members:
            start = self.faker.date_between("-3y", "-1y")
            memberships.append(
                Membership(
                    start_date=start,
                    end_date=self.faker.past_date(start),
                    user=old,
                    role=random.choice(list(settings.SITH_CLUB_ROLES.keys())),
                    club=club,
                )
            )
        for member, role in zip_roles(members):
            start = self.faker.past_date("-1y")
            memberships.append(
                Membership(
                    start_date=start,
                    user=member,
                    role=role,
                    club=club,
                )
            )
        memberships = Membership.objects.bulk_create(memberships)
        Membership._add_club_groups(memberships)

    def create_uvs(self):
        root = User.objects.get(username="root")
        categories = ["CS", "TM", "OM", "QC", "EC"]
        branches = ["TC", "GMC", "GI", "EDIM", "E", "IMSI", "HUMA"]
        languages = ["FR", "FR", "EN"]
        semesters = ["AUTUMN", "SPRING", "AUTUMN_AND_SPRING"]
        teachers = [self.faker.name() for _ in range(50)]
        uvs = []
        for _ in range(1000):
            code = (
                self.faker.random_uppercase_letter()
                + self.faker.random_uppercase_letter()
                + str(random.randint(10, 90))
            )
            uvs.append(
                UV(
                    code=code,
                    author=root,
                    manager=random.choice(teachers),
                    title=self.faker.text(max_nb_chars=50),
                    department=random.choice(branches),
                    credit_type=random.choice(categories),
                    credits=6,
                    semester=random.choice(semesters),
                    language=random.choice(languages),
                    program=self.faker.paragraph(random.randint(3, 10)),
                    skills="\n* ".join(self.faker.sentences(random.randint(3, 10))),
                    key_concepts="\n* ".join(
                        self.faker.sentences(random.randint(3, 10))
                    ),
                    hours_CM=random.randint(15, 40),
                    hours_TD=random.randint(15, 40),
                    hours_TP=random.randint(15, 40),
                    hours_THE=random.randint(15, 40),
                    hours_TE=random.randint(15, 40),
                )
            )
        UV.objects.bulk_create(uvs, ignore_conflicts=True)

    def create_products(self):
        categories = [
            ProductType(name=self.faker.text(max_nb_chars=30)) for _ in range(10)
        ]
        ProductType.objects.bulk_create(categories)
        categories = list(
            ProductType.objects.filter(name__in=[c.name for c in categories])
        )
        ae = Club.objects.get(id=settings.SITH_MAIN_CLUB_ID)
        other_clubs = random.sample(list(Club.objects.all()), k=3)
        groups = list(
            Group.objects.filter(
                id__in=[
                    settings.SITH_GROUP_SUBSCRIBERS_ID,
                    settings.SITH_GROUP_OLD_SUBSCRIBERS_ID,
                    settings.SITH_GROUP_PUBLIC_ID,
                ]
            )
        )
        counters = list(
            Counter.objects.filter(name__in=["Foyer", "MDE", "La Gommette", "Eboutic"])
        )
        # 2/3 of the products are owned by AE
        clubs = [ae, ae, ae, ae, ae, ae, *other_clubs]
        products = []
        buying_groups = []
        selling_places = []
        for _ in range(200):
            price = random.randint(0, 10) + random.choice([0, 0.25, 0.5, 0.75])
            product = Product(
                name=self.faker.text(max_nb_chars=30),
                description=self.faker.text(max_nb_chars=120),
                product_type=random.choice(categories),
                code="".join(self.faker.random_letters(length=random.randint(4, 8))),
                purchase_price=price,
                selling_price=price,
                special_selling_price=price - min(0.5, price),
                club=random.choice(clubs),
                limit_age=0 if random.random() > 0.2 else 18,
                archived=bool(random.random() > 0.7),
            )
            products.append(product)
            # there will be products without buying groups
            # but there are also such products in the real database
            buying_groups.extend(
                Product.buying_groups.through(product=product, group=group)
                for group in random.sample(groups, k=random.randint(0, 3))
            )
            selling_places.extend(
                Counter.products.through(counter=counter, product=product)
                for counter in random.sample(counters, random.randint(0, 4))
            )
        Product.objects.bulk_create(products)
        Product.buying_groups.through.objects.bulk_create(buying_groups)
        Counter.products.through.objects.bulk_create(selling_places)

    def create_sales(self, sellers: list[User]):
        customers = list(
            Customer.objects.annotate(
                since=Subquery(
                    Subscription.objects.filter(member__customer=OuterRef("pk"))
                    .annotate(res=Min("subscription_start"))
                    .values("res")
                    .order_by("res")[:1]
                )
            )
        )
        products = list(Product.objects.all())
        counters = list(
            Counter.objects.filter(name__in=["Foyer", "MDE", "La Gommette"])
        )
        sales = []
        reloads = []
        for customer in customers:
            # the longer the customer has existed, the higher the mean of nb_products
            mu = 5 + (now().year - customer.since.year) * 2
            nb_sales = max(0, int(random.normalvariate(mu=mu, sigma=mu * 5)))
            favoured_products = random.sample(products, k=(random.randint(1, 5)))
            favoured_counter = random.choice(counters)
            this_customer_sales = []
            for _ in range(nb_sales):
                product = (
                    random.choice(favoured_products)
                    if random.random() > 0.7
                    else random.choice(products)
                )
                counter = (
                    favoured_counter
                    if random.random() > 0.7
                    else random.choice(counters)
                )
                this_customer_sales.append(
                    Selling(
                        product=product,
                        counter=counter,
                        club_id=product.club_id,
                        quantity=random.randint(1, 5),
                        unit_price=product.selling_price,
                        seller=random.choice(sellers),
                        customer=customer,
                        date=make_aware(
                            self.faker.date_time_between(customer.since, localdate())
                        ),
                    )
                )
            total_expanse = sum(s.unit_price * s.quantity for s in this_customer_sales)
            total_reloaded = 0
            while total_reloaded < total_expanse:
                amount = random.choice(list(range(5, 51, 5)))
                total_reloaded += amount
                reloads.append(
                    Refilling(
                        counter=random.choice(counters),
                        amount=amount,
                        operator=random.choice(sellers),
                        customer=customer,
                        date=make_aware(
                            self.faker.date_time_between(customer.since, localdate())
                        ),
                        is_validated=True,
                    )
                )
            sales.extend(this_customer_sales)
        Refilling.objects.bulk_create(reloads)
        Selling.objects.bulk_create(sales)
        Customer.objects.update_amount()

    def create_permanences(self, sellers: list[User]):
        counters = list(
            Counter.objects.filter(name__in=["Foyer", "MDE", "La Gommette"])
        )
        perms = []
        for seller in sellers:
            favoured_counter = random.choice(counters)
            nb_perms = abs(int(random.normalvariate(mu=275, sigma=100)))
            active_period_start = self.faker.past_date("-10y")
            active_period_end = self.faker.date_between(
                active_period_start,
                min(localdate(), active_period_start + relativedelta(years=5)),
            )
            for _ in range(nb_perms):
                counter = (
                    favoured_counter
                    if random.random() > 0.8
                    else random.choice(counters)
                )
                duration = self.faker.time_delta(timedelta(hours=1))
                start = make_aware(
                    self.faker.date_time_between(active_period_start, active_period_end)
                )
                perms.append(
                    Permanency(
                        counter=counter, user=seller, start=start, end=start + duration
                    )
                )
        Permanency.objects.bulk_create(perms)

    def create_forums(self):
        users = list(User.objects.all())
        forumers = random.sample(users, math.ceil(len(users) / 10))
        most_actives = random.sample(forumers, math.ceil(len(forumers) / 6))
        categories = list(Forum.objects.filter(is_category=True))
        new_forums = [
            Forum(name=self.faker.text(20), parent=random.choice(categories))
            for _ in range(15)
        ]
        Forum.objects.bulk_create(new_forums)
        forums = list(Forum.objects.filter(is_category=False))
        new_topics = [
            ForumTopic(
                _title=self.faker.text(20),
                author=random.choice(most_actives),
                forum=random.choice(forums),
            )
            for _ in range(100)
        ]
        ForumTopic.objects.bulk_create(new_topics)
        topics = list(ForumTopic.objects.all())

        def get_author():
            if random.random() > 0.5:
                return random.choice(most_actives)
            return random.choice(forumers)

        messages = []
        for t in topics:
            nb_messages = max(1, int(random.normalvariate(mu=90, sigma=50)))
            dates = sorted(
                [
                    self.faker.date_time_between("-15y", "-1d", tzinfo=tz.utc)
                    for _ in range(nb_messages)
                ],
                reverse=True,
            )
            messages.extend(
                [
                    ForumMessage(
                        topic=t,
                        author=get_author(),
                        date=d,
                        message="\n\n".join(
                            self.faker.paragraphs(random.randint(1, 4))
                        ),
                    )
                    for d in dates
                ]
            )
        ForumMessage.objects.bulk_create(messages)
        ForumTopic.objects.update(
            _message_number=Subquery(
                ForumMessage.objects.filter(topic_id=OuterRef("pk"))
                .values("topic_id")
                .annotate(res=Count("*"))
                .values("res")
            ),
            _last_message_id=Subquery(
                ForumMessage.objects.order_by("-date").values("id")[:1]
            ),
        )
        for f in Forum.objects.filter(parent__isnull=False):
            # this is a N+1 queries, but it's ok,
            # since there are quite a few forums
            # and trying to do it with a single query
            # would result in a big whibbly-woobly hacky queryset
            f.set_last_message()
            f.set_topic_number()
