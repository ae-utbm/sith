import MySQLdb
import os
import django
import random
import datetime
from io import StringIO
from pytz import timezone
from os import listdir

os.environ["DJANGO_SETTINGS_MODULE"] = "sith.settings"
os.environ['DJANGO_COLORS'] = 'nocolor'
django.setup()

from django.db import IntegrityError
from django.conf import settings
from django.core.management import call_command
from django.db import connection
from django.forms import ValidationError
from django.core.files import File


from core.models import User, SithFile
from club.models import Club, Membership
from counter.models import Customer, Counter, Selling, Refilling, Product, ProductType, Permanency, Eticket
from subscription.models import Subscription
from eboutic.models import Invoice, InvoiceItem
from accounting.models import BankAccount, ClubAccount, GeneralJournal, Operation, AccountingType, Company, SimplifiedAccountingType, Label
from sas.models import Album, Picture, PeoplePictureRelation

db = MySQLdb.connect(**settings.OLD_MYSQL_INFOS)
start = datetime.datetime.now()

def reset_index(*args):
    sqlcmd = StringIO()
    call_command("sqlsequencereset", *args, stdout=sqlcmd)
    cursor = connection.cursor()
    cursor.execute(sqlcmd.getvalue())

def to_unicode(s):
    if s:
        return bytes(s, 'cp1252', errors="replace").decode('utf-8', errors='replace')
    return ""


def migrate_core():
    def migrate_users():
        SEX = {'1': 'MAN', '2': 'WOMAN', None: 'MAN'}
        TSHIRT = {
                None: '-',
                '': '-',
                'NULL': '-',
                'XS': 'XS',
                'S': 'S',
                'M': 'M',
                'L': 'L',
                'XL': 'XL',
                'XXL': 'XXL',
                'XXXL': 'XXXL',
                }
        ROLE = {
                'doc': 'DOCTOR',
                'etu': 'STUDENT',
                'anc': 'FORMER STUDENT',
                'ens': 'TEACHER',
                'adm': 'ADMINISTRATIVE',
                'srv': 'SERVICE',
                'per': 'AGENT',
                None: '',
                }
        DEPARTMENTS = {
                'tc': 'TC',
                'gi': 'GI',
                'gesc': 'GESC',
                'na': 'NA',
                'mc': 'MC',
                'imap': 'IMAP',
                'huma': 'HUMA',
                'edim': 'EDIM',
                'ee': 'EE',
                'imsi': 'IMSI',
                'truc': 'NA',
                None: 'NA',
                }

        def get_random_free_email():
            email = "no_email_%s@git.an" % random.randrange(4000, 40000)
            while User.objects.filter(email=email).exists():
                email = "no_email_%s@git.an" % random.randrange(4000, 40000)
            return email

        c = db.cursor(MySQLdb.cursors.SSDictCursor)
        c.execute("""
        SELECT *
        FROM utilisateurs utl
        LEFT JOIN utl_etu ue
        ON ue.id_utilisateur = utl.id_utilisateur
        LEFT JOIN utl_etu_utbm ueu
        ON ueu.id_utilisateur = utl.id_utilisateur
        LEFT JOIN utl_extra uxtra
        ON uxtra.id_utilisateur = utl.id_utilisateur
        LEFT JOIN loc_ville ville
        ON utl.id_ville = ville.id_ville
        -- WHERE utl.id_utilisateur = 9360
        """)
        User.objects.filter(id__gt=0).delete()
        print("Users deleted")

        for u in c:
            try:
                new = User(
                        id=u['id_utilisateur'],
                        last_name=to_unicode(u['nom_utl']) or "Bou",
                        first_name=to_unicode(u['prenom_utl']) or "Bi",
                        email=u['email_utl'],
                        second_email=u['email_utbm'] or "",
                        date_of_birth=u['date_naissance_utl'],
                        last_update=u['date_maj_utl'],
                        nick_name=to_unicode(u['surnom_utbm']),
                        sex=SEX[u['sexe_utl']],
                        tshirt_size=TSHIRT[u['taille_tshirt_utl']],
                        role=ROLE[u['role_utbm']],
                        department=DEPARTMENTS[u['departement_utbm']],
                        dpt_option=to_unicode(u['filiere_utbm']),
                        semester=u['semestre_utbm'] or 0,
                        quote=to_unicode(u['citation']),
                        school=to_unicode(u['nom_ecole_etudiant']),
                        promo=u['promo_utbm'] or 0,
                        forum_signature=to_unicode(u['signature_utl']),
                        address=(to_unicode(u['addresse_utl']) + ", " + to_unicode(u['cpostal_ville']) + " " + to_unicode(u['nom_ville'])),
                        parent_address=(to_unicode(u['adresse_parents']) + ", " + to_unicode(u['cpostal_parents']) + " " + to_unicode(u['ville_parents'])),
                        phone=u['tel_portable_utl'] or "",
                        parent_phone=u['tel_parents'] or "",
                        is_subscriber_viewable=bool(u['publique_utl']),
                )
                new.generate_username()
                new.set_password(str(random.randrange(1000000, 10000000)))
                new.save()
            except IntegrityError as e:
                if "Key (email)" in repr(e):
                    new.email = get_random_free_email()
                    new.save()
                    print("New email generated")
                else:
                    print("FAIL for user %s: %s" % (u['id_utilisateur'], repr(e)))
            except Exception as e:
                print("FAIL for user %s: %s" % (u['id_utilisateur'], repr(e)))
        c.close()
        print("Users migrated at %s" % datetime.datetime.now())
        print("Running time: %s" % (datetime.datetime.now()-start))

    def migrate_profile_pict():
        PROFILE_ROOT = "/data/matmatronch/"

        profile = SithFile.objects.filter(parent=None, name="profiles").first()
        profile.children.all().delete()
        print("Profiles pictures deleted")
        for filename in listdir(PROFILE_ROOT):
            if filename.split('.')[-2] != "mini":
                try:
                    uid = filename.split('.')[0].split('-')[0]
                    user = User.objects.filter(id=int(uid)).first()
                    if user:
                        f = File(open(PROFILE_ROOT + '/' + filename, 'rb'))
                        f.name = f.name.split('/')[-1]
                        t = filename.split('.')[1]
                        new_file = SithFile(parent=profile, name=filename,
                                file=f, owner=user, is_folder=False, mime_type="image/jpeg", size=f.size)
                        if t == "identity":
                            new_file.save()
                            user.profile_pict = new_file
                            user.save()
                        elif t == "blouse":
                            new_file.save()
                            user.scrub_pict = new_file
                            user.save()
                        else:
                            new_file.save()
                            user.avatar_pict = new_file
                            user.save()
                except Exception as e:
                    print(repr(e))
        print("Profile pictures migrated at %s" % datetime.datetime.now())
        print("Running time: %s" % (datetime.datetime.now()-start))

    migrate_users()
    migrate_profile_pict()


def migrate_club():
    def migrate_clubs():
        cur = db.cursor(MySQLdb.cursors.SSDictCursor)
        cur.execute("""
        SELECT *
        FROM asso asso
        WHERE nom_unix_asso <> "ae"
            AND nom_unix_asso <> "bdf"
            AND nom_unix_asso <> "laverie"
        """)
        # club = cur.fetchone()
        # for k,v in club.items():
        #     print("%40s | %40s" % (k, v))

        for c in cur:
            try:
                new = Club(
                        id=c['id_asso'],
                        name=to_unicode(c['nom_asso']),
                        unix_name=to_unicode(c['nom_unix_asso']),
                        address=to_unicode(c['adresse_postale']),
                        )
                new.save()
            except Exception as e:
                    print("FAIL for club %s: %s" % (c['nom_unix_asso'], repr(e)))
        cur.execute("""
        SELECT *
        FROM asso
        """)
        for c in cur:
            club = Club.objects.filter(id=c['id_asso']).first()
            parent = Club.objects.filter(id=c['id_asso_parent']).first()
            club.parent = parent
            club.save()
        cur.close()
        print("Clubs migrated at %s" % datetime.datetime.now())
        print("Running time: %s" % (datetime.datetime.now()-start))

    def migrate_club_memberships():
        cur = db.cursor(MySQLdb.cursors.SSDictCursor)
        cur.execute("""
        SELECT *
        FROM asso_membre
        """)

        Membership.objects.all().delete()
        print("Memberships deleted")
        for m in cur:
            try:
                club = Club.objects.filter(id=m['id_asso']).first()
                user = User.objects.filter(id=m['id_utilisateur']).first()
                if club and user:
                    new = Membership(
                            id=Membership.objects.count()+1,
                            club=club,
                            user=user,
                            start_date=m['date_debut'],
                            end_date=m['date_fin'],
                            role=m['role'],
                            description=to_unicode(m['desc_role']),
                            )
                    new.save()
            except Exception as e:
                    print("FAIL for club membership %s: %s" % (m['id_asso'], repr(e)))
        cur.close()
        print("Clubs memberships migrated at %s" % datetime.datetime.now())
        print("Running time: %s" % (datetime.datetime.now()-start))

    # migrate_clubs()
    migrate_club_memberships()

def migrate_subscriptions():
    LOCATION = {
            5: "SEVENANS",
            6: "BELFORT",
            9: "MONTBELIARD",
            None: "SEVENANS",
            }
    TYPE = {
            0: 'un-semestre',
            1: 'deux-semestres',
            2: 'cursus-tronc-commun',
            3: 'cursus-branche',
            4: 'membre-honoraire',
            5: 'assidu',
            6: 'amicale/doceo',
            7: 'reseau-ut',
            8: 'crous',
            9: 'sbarro/esta',
            10: 'cursus-alternant',
            None: 'un-semestre',
            }
    PAYMENT = {
            1: "CHECK",
            2: "CARD",
            3: "CASH",
            4: "OTHER",
            5: "EBOUTIC",
            0: "OTHER",
            }
    cur = db.cursor(MySQLdb.cursors.SSDictCursor)
    cur.execute("""
    SELECT *
    FROM ae_cotisations
    """)

    Subscription.objects.all().delete()
    print("Subscriptions deleted")
    Customer.objects.all().delete()
    print("Customers deleted")
    for r in cur:
        try:
            user = User.objects.filter(id=r['id_utilisateur']).first()
            if user:
                new = Subscription(
                        id=r['id_cotisation'],
                        member=user,
                        subscription_start=r['date_cotis'],
                        subscription_end=r['date_fin_cotis'],
                        subscription_type=TYPE[r['type_cotis']],
                        payment_method=PAYMENT[r['mode_paiement_cotis']],
                        location=LOCATION[r['id_comptoir']],
                        )
                new.save()
        except Exception as e:
                print("FAIL for subscription %s: %s" % (r['id_cotisation'], repr(e)))
    cur.close()
    print("Subscriptions migrated at %s" % datetime.datetime.now())
    print("Running time: %s" % (datetime.datetime.now()-start))

def migrate_counter():
    def update_customer_account():
        cur = db.cursor(MySQLdb.cursors.SSDictCursor)
        cur.execute("""
        SELECT *
        FROM ae_carte carte
        JOIN ae_cotisations cotis
        ON carte.id_cotisation = cotis.id_cotisation
        """)
        for r in cur:
            try:
                user = Customer.objects.filter(user_id=r['id_utilisateur']).first()
                if user:
                    user.account_id = str(r['id_carte_ae']) + r['cle_carteae'].lower()
                    user.save()
            except Exception as e:
                    print("FAIL to update customer account for %s: %s" % (r['id_cotisation'], repr(e)))
        cur.close()
        print("Customer accounts migrated at %s" % datetime.datetime.now())
        print("Running time: %s" % (datetime.datetime.now()-start))

    def migrate_counters():
        cur = db.cursor(MySQLdb.cursors.SSDictCursor)
        cur.execute("""
        SELECT *
        FROM cpt_comptoir
        """)
        Counter.objects.all().delete()
        for r in cur:
            try:
                club = Club.objects.filter(id=r['id_assocpt']).first()
                new = Counter(
                        id=r['id_comptoir'],
                        name=to_unicode(r['nom_cpt']),
                        club=club,
                        type="OFFICE",
                        )
                new.save()
            except Exception as e:
                    print("FAIL to migrate counter %s: %s" % (r['id_comptoir'], repr(e)))
        cur.close()
        eboutic = Counter.objects.filter(id=3).first()
        eboutic.type = "EBOUTIC"
        eboutic.save()
        print("Counters migrated at %s" % datetime.datetime.now())
        print("Running time: %s" % (datetime.datetime.now()-start))

    def reset_customer_amount():
        Refilling.objects.all().delete()
        Selling.objects.all().delete()
        Invoice.objects.all().delete()
        for c in Customer.objects.all():
            c.amount = 0
            c.save()
        print("Customer amount reset")

    def migrate_refillings():
        BANK = {
                0: "OTHER",
                1: "SOCIETE-GENERALE",
                2: "BANQUE-POPULAIRE",
                3: "BNP",
                4: "CAISSE-EPARGNE",
                5: "CIC",
                6: "CREDIT-AGRICOLE",
                7: "CREDIT-MUTUEL",
                8: "CREDIT-LYONNAIS",
                9: "LA-POSTE",
                100: "OTHER",
                None: "OTHER",
                }
        PAYMENT = {
                2: "CARD",
                1: "CASH",
                0: "CHECK",
                }
        cur = db.cursor(MySQLdb.cursors.SSDictCursor)
        cur.execute("""
        SELECT *
        FROM cpt_rechargements
        """)
        root_cust = Customer.objects.filter(user__id=0).first()
        mde = Counter.objects.filter(id=1).first()
        Refilling.objects.all().delete()
        print("Refillings deleted")
        fail = 100
        for r in cur:
            try:
                cust = Customer.objects.filter(user__id=r['id_utilisateur']).first()
                user = User.objects.filter(id=r['id_utilisateur']).first()
                if not cust:
                    if not user:
                        cust = root_cust
                    else:
                        cust = Customer(user=user, amount=0, account_id=Customer.generate_account_id(fail))
                        cust.save()
                        fail += 1
                op = User.objects.filter(id=r['id_utilisateur_operateur']).first()
                counter = Counter.objects.filter(id=r['id_comptoir']).first()
                new = Refilling(
                        id=r['id_rechargement'],
                        counter=counter or mde,
                        customer=cust or root_cust,
                        operator=op or root_cust.user,
                        amount=r['montant_rech']/100,
                        payment_method=PAYMENT[r['type_paiement_rech']],
                        bank=BANK[r['banque_rech']],
                        date=r['date_rech'].replace(tzinfo=timezone('Europe/Paris')),
                        )
                new.save()
            except Exception as e:
                    print("FAIL to migrate refilling %s for %s: %s" % (r['id_rechargement'], r['id_utilisateur'], repr(e)))
        cur.close()
        print("Refillings migrated at %s" % datetime.datetime.now())
        print("Running time: %s" % (datetime.datetime.now()-start))

    def migrate_typeproducts():
        cur = db.cursor(MySQLdb.cursors.SSDictCursor)
        cur.execute("""
        SELECT *
        FROM cpt_type_produit
        """)
        ProductType.objects.all().delete()
        print("Product types deleted")
        for r in cur:
            try:
                new = ProductType(
                        id=r['id_typeprod'],
                        name=to_unicode(r['nom_typeprod']),
                        description=to_unicode(r['description_typeprod']),
                        )
                new.save()
            except Exception as e:
                    print("FAIL to migrate product type %s: %s" % (r['nom_typeprod'], repr(e)))
        cur.close()
        print("Product types migrated at %s" % datetime.datetime.now())
        print("Running time: %s" % (datetime.datetime.now()-start))

    def migrate_products():
        cur = db.cursor(MySQLdb.cursors.SSDictCursor)
        cur.execute("""
        SELECT *
        FROM cpt_produits
        """)
        Product.objects.all().delete()
        print("Product deleted")
        for r in cur:
            try:
                type = ProductType.objects.filter(id=r['id_typeprod']).first()
                club = Club.objects.filter(id=r['id_assocpt']).first()
                new = Product(
                        id=r['id_produit'],
                        product_type=type,
                        name=to_unicode(r['nom_prod']),
                        description=to_unicode(r['description_prod']),
                        code=to_unicode(r['cbarre_prod']),
                        purchase_price=r['prix_achat_prod']/100,
                        selling_price=r['prix_vente_prod']/100,
                        special_selling_price=r['prix_vente_barman_prod']/100,
                        club=club,
                        limit_age=r['mineur'] or 0,
                        tray=bool(r['plateau']),
                        )
                new.save()
            except Exception as e:
                    print("FAIL to migrate product %s: %s" % (r['nom_prod'], repr(e)))
        cur.close()
        print("Product migrated at %s" % datetime.datetime.now())
        print("Running time: %s" % (datetime.datetime.now()-start))

    def migrate_product_pict():
        FILE_ROOT = "/data/files/"

        cur = db.cursor(MySQLdb.cursors.SSDictCursor)
        cur.execute("""
        SELECT *
        FROM cpt_produits
        WHERE id_file IS NOT NULL
        """)
        for r in cur:
            try:
                prod = Product.objects.filter(id=r['id_produit']).first()
                if prod:
                    f = File(open(FILE_ROOT + '/' + str(r['id_file']) + ".1", 'rb'))
                    f.name = prod.name
                    prod.icon = f
                    prod.save()
            except Exception as e:
                print(repr(e))
        print("Product pictures migrated at %s" % datetime.datetime.now())
        print("Running time: %s" % (datetime.datetime.now()-start))

    def migrate_products_to_counter():
        cur = db.cursor(MySQLdb.cursors.SSDictCursor)
        cur.execute("""
        SELECT *
        FROM cpt_mise_en_vente
        """)
        for r in cur:
            try:
                product = Product.objects.filter(id=r['id_produit']).first()
                counter = Counter.objects.filter(id=r['id_comptoir']).first()
                counter.products.add(product)
                counter.save()
            except Exception as e:
                    print("FAIL to set product %s in counter %s: %s" % (product, counter, repr(e)))
        cur.close()
        print("Product in counters migrated at %s" % datetime.datetime.now())
        print("Running time: %s" % (datetime.datetime.now()-start))

    def migrate_invoices():
        cur = db.cursor(MySQLdb.cursors.SSDictCursor)
        cur.execute("""
        SELECT *
        FROM cpt_vendu ven
        LEFT JOIN cpt_debitfacture fac
        ON ven.id_facture = fac.id_facture
        WHERE fac.mode_paiement = 'SG'
        """)
        Invoice.objects.all().delete()
        print("Invoices deleted")
        Refilling.objects.filter(payment_method="CARD").delete()
        print("Card refillings deleted")
        Selling.objects.filter(payment_method="CARD").delete()
        print("Card sellings deleted")
        root = User.objects.filter(id=0).first()
        for r in cur:
            try:
                product = Product.objects.filter(id=r['id_produit']).first()
                user = User.objects.filter(id=r['id_utilisateur_client']).first()
                i = Invoice.objects.filter(id=r['id_facture']).first() or Invoice(id=r['id_facture'])
                i.user = user or root
                for f in i._meta.local_fields:
                    if f.name == "date":
                        f.auto_now = False
                i.date = r['date_facture'].replace(tzinfo=timezone('Europe/Paris'))
                i.save()
                InvoiceItem(invoice=i, product_id=product.id, product_name=product.name, type_id=product.product_type.id,
                        product_unit_price=r['prix_unit']/100, quantity=r['quantite']).save()
            except ValidationError as e:
                print(repr(e) + " for %s (%s)" % (customer, customer.user.id))
            except Exception as e:
                print("FAIL to migrate invoice %s: %s" % (r['id_facture'], repr(e)))
        cur.close()
        for i in Invoice.objects.all():
            for f in i._meta.local_fields:
                if f.name == "date":
                    f.auto_now = False
            i.validate()
        print("Invoices migrated at %s" % datetime.datetime.now())
        print("Running time: %s" % (datetime.datetime.now()-start))

    def migrate_sellings():
        cur = db.cursor(MySQLdb.cursors.SSDictCursor)
        cur.execute("""
        SELECT *
        FROM cpt_vendu ven
        LEFT JOIN cpt_debitfacture fac
        ON ven.id_facture = fac.id_facture
        WHERE fac.mode_paiement = 'AE'
        """)
        Selling.objects.filter(payment_method="SITH_ACCOUNT").delete()
        print("Sith account selling deleted")
        for c in Customer.objects.all():
            c.amount = sum([r.amount for r in c.refillings.all()])
            c.save()
        print("Customer amount reset to sum of refillings")
        ae = Club.objects.filter(unix_name="ae").first()
        mde = Counter.objects.filter(id=1).first()
        root = User.objects.filter(id=0).first()
        beer = Product.objects.filter(id=1).first()
        for r in cur:
            try:
                product = Product.objects.filter(id=r['id_produit']).first() or beer
                club = Club.objects.filter(id=r['id_assocpt']).first() or ae
                counter = Counter.objects.filter(id=r['id_comptoir']).first() or mde
                op = User.objects.filter(id=r['id_utilisateur']).first() or root
                customer = Customer.objects.filter(user__id=r['id_utilisateur_client']).first() or root.customer
                new = Selling(
                        label=product.name or "Produit inexistant",
                        counter=counter,
                        club=club,
                        product=product,
                        seller=op,
                        customer=customer,
                        unit_price=r['prix_unit']/100,
                        quantity=r['quantite'],
                        payment_method="SITH_ACCOUNT",
                        date=r['date_facture'].replace(tzinfo=timezone('Europe/Paris')),
                        )
                new.save()
            except ValidationError as e:
                print(repr(e) + " for %s (%s)" % (customer, customer.user.id))
            except Exception as e:
                print("FAIL to migrate selling %s: %s" % (r['id_facture'], repr(e)))
        cur.close()
        print("Sellings migrated at %s" % datetime.datetime.now())
        print("Running time: %s" % (datetime.datetime.now()-start))

    def migrate_permanencies():
        cur = db.cursor(MySQLdb.cursors.SSDictCursor)
        cur.execute("""
        SELECT *
        FROM cpt_tracking
        """)
        Permanency.objects.all().delete()
        print("Permanencies deleted")
        for r in cur:
            try:
                counter = Counter.objects.filter(id=r['id_comptoir']).first()
                user = User.objects.filter(id=r['id_utilisateur']).first()
                new = Permanency(
                        user=user,
                        counter=counter,
                        start=r['logged_time'].replace(tzinfo=timezone('Europe/Paris')),
                        activity=r['logged_time'].replace(tzinfo=timezone('Europe/Paris')),
                        end=r['closed_time'].replace(tzinfo=timezone('Europe/Paris')),
                        )
                new.save()
            except Exception as e:
                print("FAIL to migrate permanency: %s" % (repr(e)))
        cur.close()
        print("Permanencies migrated at %s" % datetime.datetime.now())
        print("Running time: %s" % (datetime.datetime.now()-start))

    update_customer_account()
    migrate_counters()
    migrate_permanencies()
    migrate_typeproducts()
    migrate_products()
    migrate_product_pict()
    migrate_products_to_counter()
    reset_customer_amount()
    migrate_invoices()
    migrate_refillings()
    migrate_sellings()

def check_accounts():
    cur = db.cursor(MySQLdb.cursors.SSDictCursor)
    cur.execute("""
    SELECT *
    FROM utilisateurs
    """)
    mde = Counter.objects.filter(id=1).first()
    ae = Club.objects.filter(unix_name='ae').first()
    root = User.objects.filter(id=0).first()
    for r in cur:
        if r['montant_compte'] and r['montant_compte'] > 0:
            try:
                cust = Customer.objects.filter(user__id=r['id_utilisateur']).first()
                if int(cust.amount * 100) != r['montant_compte']:
                    print("Adding %s to %s's account" % (float(cust.amount) - (r['montant_compte']/100), cust.user))
                    new = Selling(
                            label="Ajustement migration base de donnée",
                            counter=mde,
                            club=ae,
                            product=None,
                            seller=root,
                            customer=cust,
                            unit_price=float(cust.amount) - (r['montant_compte']/100.),
                            quantity=1,
                            payment_method="SITH_ACCOUNT",
                            )
                    new.save()
            except Exception as e:
                print("FAIL to adjust user account: %s" % (repr(e)))
### Accounting

def migrate_accounting():
    def migrate_companies():
        cur = db.cursor(MySQLdb.cursors.SSDictCursor)
        cur.execute("""
        SELECT *
        FROM entreprise
        """)
        Company.objects.all().delete()
        print("Company deleted")
        for r in cur:
            try:
                new = Company(
                        id=r['id_ent'],
                        name=to_unicode(r['nom_entreprise']),
                        street=to_unicode(r['rue_entreprise']),
                        city=to_unicode(r['ville_entreprise']),
                        postcode=to_unicode(r['cpostal_entreprise']),
                        country=to_unicode(r['pays_entreprise']),
                        phone=to_unicode(r['telephone_entreprise']),
                        email=to_unicode(r['email_entreprise']),
                        website=to_unicode(r['siteweb_entreprise']),
                        )
                new.save()
            except Exception as e:
                print("FAIL to migrate company: %s" % (repr(e)))
        cur.close()
        print("Companies migrated at %s" % datetime.datetime.now())
        print("Running time: %s" % (datetime.datetime.now()-start))

    def migrate_bank_accounts():
        cur = db.cursor(MySQLdb.cursors.SSDictCursor)
        cur.execute("""
        SELECT *
        FROM cpta_cpbancaire
        """)
        BankAccount.objects.all().delete()
        print("Bank accounts deleted")
        ae = Club.objects.filter(unix_name='ae').first()
        for r in cur:
            try:
                new = BankAccount(
                        id=r['id_cptbc'],
                        club=ae,
                        name=to_unicode(r['nom_cptbc']),
                        )
                new.save()
            except Exception as e:
                print("FAIL to migrate bank account: %s" % (repr(e)))
        cur.close()
        print("Bank accounts migrated at %s" % datetime.datetime.now())
        print("Running time: %s" % (datetime.datetime.now()-start))

    def migrate_club_accounts():
        cur = db.cursor(MySQLdb.cursors.SSDictCursor)
        cur.execute("""
        SELECT *
        FROM cpta_cpasso
        """)
        ClubAccount.objects.all().delete()
        print("Club accounts deleted")
        ae = Club.objects.filter(id=1).first()
        for r in cur:
            try:
                club = Club.objects.filter(id=r['id_asso']).first() or ae
                bank_acc = BankAccount.objects.filter(id=r['id_cptbc']).first()
                new = ClubAccount(
                        id=r['id_cptasso'],
                        club=club,
                        name=club.name[:30],
                        bank_account=bank_acc,
                        )
                new.save()
            except Exception as e:
                print("FAIL to migrate club account: %s" % (repr(e)))
        cur.close()
        print("Club accounts migrated at %s" % datetime.datetime.now())
        print("Running time: %s" % (datetime.datetime.now()-start))

    def migrate_journals():
        cur = db.cursor(MySQLdb.cursors.SSDictCursor)
        cur.execute("""
        SELECT *
        FROM cpta_classeur
        """)
        GeneralJournal.objects.all().delete()
        print("General journals deleted")
        for r in cur:
            try:
                club_acc = ClubAccount.objects.filter(id=r['id_cptasso']).first()
                new = GeneralJournal(
                        id=r['id_classeur'],
                        club_account=club_acc,
                        name=to_unicode(r['nom_classeur']),
                        start_date=r['date_debut_classeur'],
                        end_date=r['date_fin_classeur'],
                        closed=bool(r['ferme']),
                        )
                new.save()
            except Exception as e:
                print("FAIL to migrate general journal: %s" % (repr(e)))
        cur.close()
        print("General journals migrated at %s" % datetime.datetime.now())
        print("Running time: %s" % (datetime.datetime.now()-start))

    def migrate_accounting_types():
        MOVEMENT = {
                -1: "DEBIT",
                0: "NEUTRAL",
                1: "CREDIT",
                }
        cur = db.cursor(MySQLdb.cursors.SSDictCursor)
        cur.execute("""
        SELECT *
        FROM cpta_op_plcptl
        """)
        AccountingType.objects.all().delete()
        print("Accounting types deleted")
        for r in cur:
            try:
                new = AccountingType(
                        id=r['id_opstd'],
                        code=str(r['code_plan']),
                        label=to_unicode(r['libelle_plan']).capitalize(),
                        movement_type=MOVEMENT[r['type_mouvement']],
                        )
                new.save()
            except Exception as e:
                print("FAIL to migrate accounting type: %s" % (repr(e)))
        cur.close()
        print("Accounting types migrated at %s" % datetime.datetime.now())
        print("Running time: %s" % (datetime.datetime.now()-start))

    def migrate_simpleaccounting_types():
        cur = db.cursor(MySQLdb.cursors.SSDictCursor)
        cur.execute("""
        SELECT *
        FROM cpta_op_clb
        WHERE id_asso IS NULL
        """)
        SimplifiedAccountingType.objects.all().delete()
        print("Simple accounting types deleted")
        for r in cur:
            try:
                at = AccountingType.objects.filter(id=r['id_opstd']).first()
                new = SimplifiedAccountingType(
                        id=r['id_opclb'],
                        label=to_unicode(r['libelle_opclb']).capitalize(),
                        accounting_type=at,
                        )
                new.save()
            except Exception as e:
                print("FAIL to migrate simple type: %s" % (repr(e)))
        cur.close()
        print("Simple accounting types migrated at %s" % datetime.datetime.now())
        print("Running time: %s" % (datetime.datetime.now()-start))

    def migrate_labels():
        cur = db.cursor(MySQLdb.cursors.SSDictCursor)
        cur.execute("""
        SELECT *
        FROM cpta_libelle
        WHERE id_asso IS NOT NULL
        """)
        Label.objects.all().delete()
        print("Labels deleted")
        for r in cur:
            try:
                club_accounts = ClubAccount.objects.filter(club__id=r['id_asso']).all()
                for ca in club_accounts:
                    new = Label(
                            club_account=ca,
                            name=to_unicode(r['nom_libelle']),
                            )
                    new.save()
            except Exception as e:
                print("FAIL to migrate label: %s" % (repr(e)))
        cur.close()
        print("Labels migrated at %s" % datetime.datetime.now())
        print("Running time: %s" % (datetime.datetime.now()-start))

    def migrate_operations():
        MODE = {
                1: "CHECK",
                2: "CASH",
                3: "TRANSFERT",
                4: "CARD",
                0: "CASH",
                None: "CASH",
                }
        MOVEMENT_TYPE = {
                -1: "DEBIT",
                0: "NEUTRAL",
                1: "CREDIT",
                None: "NEUTRAL",
                }
        cur = db.cursor(MySQLdb.cursors.SSDictCursor)
        cur.execute("""
        SELECT *
        FROM cpta_operation op
        LEFT JOIN cpta_op_clb clb
        ON op.id_opclb = clb.id_opclb
        LEFT JOIN cpta_libelle lab
        ON op.id_libelle = lab.id_libelle
        """)
        Operation.objects.all().delete()
        print("Operation deleted")
        for r in cur:
            try:
                simple_type = None
                accounting_type = None
                label = None
                if r['id_opclb']:
                    simple_type = SimplifiedAccountingType.objects.filter(id=r['id_opclb']).first()
                if r['id_opstd']:
                    accounting_type = AccountingType.objects.filter(id=r['id_opstd']).first()
                if not accounting_type and simple_type:
                    accounting_type = simple_type.accounting_type
                if not accounting_type:
                    accounting_type = AccountingType.objects.filter(movement_type=MOVEMENT_TYPE[r['type_mouvement']]).first()
                journal = GeneralJournal.objects.filter(id=r['id_classeur']).first()
                if r['id_libelle']:
                    label = journal.club_account.labels.filter(name=to_unicode(r['nom_libelle'])).first()
                def get_target_type():
                    if r['id_utilisateur']:
                        return "USER"
                    if r['id_asso']:
                        return "CLUB"
                    if r['id_ent']:
                        return "COMPANY"
                    if r['id_classeur']:
                        return "ACCOUNT"
                def get_target_id():
                    return int(r['id_utilisateur'] or r['id_asso'] or r['id_ent'] or r['id_classeur']) or None
                new = Operation(
                        id=r['id_op'],
                        journal=journal,
                        amount=r['montant_op']/100,
                        date=r['date_op'] or journal.end_date,
                        remark=to_unicode(r['commentaire_op']),
                        mode=MODE[r['mode_op']],
                        cheque_number=str(r['num_cheque_op']),
                        done=bool(r['op_effctue']),
                        simpleaccounting_type=simple_type,
                        accounting_type=accounting_type,
                        target_type=get_target_type(),
                        target_id=get_target_id(),
                        target_label="-",
                        label=label,
                        )
                try:
                    new.clean()
                except:
                    new.target_id = get_target_id()
                    new.target_type = "OTHER"
                new.save()
            except Exception as e:
                print("FAIL to migrate operation: %s" % (repr(e)))
        cur.close()
        print("Operations migrated at %s" % datetime.datetime.now())
        print("Running time: %s" % (datetime.datetime.now()-start))

    def make_operation_links():
        cur = db.cursor(MySQLdb.cursors.SSDictCursor)
        cur.execute("""
        SELECT *
        FROM cpta_operation
        """)
        for r in cur:
            if r['id_op_liee']:
                try:
                    op1 = Operation.objects.filter(id=r['id_op']).first()
                    op2 = Operation.objects.filter(id=r['id_op_liee']).first()
                    op1.linked_operation = op2
                    op1.save()
                    op2.linked_operation = op1
                    op2.save()
                except Exception as e:
                    print("FAIL to link operations: %s" % (repr(e)))
        cur.close()
        print("Operations links migrated at %s" % datetime.datetime.now())
        print("Running time: %s" % (datetime.datetime.now()-start))

    migrate_companies()
    migrate_accounting_types()
    migrate_simpleaccounting_types()
    migrate_bank_accounts()
    migrate_club_accounts()
    migrate_labels()
    migrate_journals()
    migrate_operations()
    make_operation_links()

def migrate_godfathers():
    cur = db.cursor(MySQLdb.cursors.SSDictCursor)
    cur.execute("""
    SELECT *
    FROM parrains
    """)
    for r in cur:
        try:
            father = User.objects.filter(id=r['id_utilisateur']).first()
            child = User.objects.filter(id=r['id_utilisateur_fillot']).first()
            father.godchildren.add(child)
            father.save()
        except Exception as e:
            print("FAIL to migrate godfathering: %s" % (repr(e)))
    cur.close()
    print("Godfathers migrated at %s" % datetime.datetime.now())
    print("Running time: %s" % (datetime.datetime.now()-start))

def migrate_etickets():
    FILE_ROOT = "/data/files/"
    cur = db.cursor(MySQLdb.cursors.SSDictCursor)
    cur.execute("""
    SELECT *
    FROM cpt_etickets
    """)
    Eticket.objects.all().delete()
    print("Etickets deleted")
    for r in cur:
        try:
            p = Product.objects.filter(id=r['id_produit']).first()
            try:
                f = File(open(FILE_ROOT + '/' + str(r['banner']) + ".1", 'rb'))
            except:
                f = None
            e = Eticket(
                    product=p,
                    secret=to_unicode(r['secret']),
                    banner=f,
                    event_title=p.name,
                    )
            e.save()
            e.secret=to_unicode(r['secret'])
            e.save()
        except Exception as e:
            print("FAIL to migrate eticket: %s" % (repr(e)))
    cur.close()
    print("Etickets migrated at %s" % datetime.datetime.now())
    print("Running time: %s" % (datetime.datetime.now()-start))

def migrate_sas():
    album_link = {}
    picture_link = {}
    FILE_ROOT = "/data/sas/"
    SithFile.objects.filter(id__gte=18892).delete()
    print("Album/Pictures deleted")
    reset_index('core', 'sas')
    cur = db.cursor(MySQLdb.cursors.SSDictCursor)
    cur.execute("""
    SELECT *
    FROM sas_cat_photos
    """)
    root = User.objects.filter(username="root").first()
    for r in cur:
        try:
            a = Album(name=to_unicode(r['nom_catph']), owner=root, is_moderated=True, parent=None)
            a.save()
            album_link[str(r['id_catph'])] = a.id
        except Exception as e:
            print("FAIL to migrate Album: %s" % (repr(e)))
    print("Album moved, need to make the tree")
    cur.execute("""
    SELECT *
    FROM sas_cat_photos
    """)
    for r in cur:
        try:
            p = Album.objects.filter(id=album_link[str(r['id_catph_parent'])]).first()
            a = Album.objects.filter(id=album_link[str(r['id_catph'])]).first()
            a.parent = p
            a.save()
        except: pass
    print("Album migrated at %s" % datetime.datetime.now())
    print("Running time: %s" % (datetime.datetime.now()-start))
    with open("albums.link", "w") as f:
        f.write(str(album_link))
    cur.close()
    finished = False
    chunk = 0
    while not finished:
        cur = db.cursor(MySQLdb.cursors.SSDictCursor)
        cur.execute("""
        SELECT *
        FROM sas_photos
        ORDER BY 'id_photo'
        LIMIT %s, 1000
        """, (chunk*1000, ))
        has_result = False
        for r in cur:
            try:
                user = User.objects.filter(id=r['id_utilisateur']).first() or root
                parent = Album.objects.filter(id=album_link[str(r['id_catph'])]).first()

                file_name = FILE_ROOT
                if r['date_prise_vue']:
                    file_name += r['date_prise_vue'].strftime("%Y/%m/%d")
                else:
                    file_name += '/'.join(["1970", "01", "01"])
                file_name += "/" + str(r['id_photo']) + ".jpg"

                file = File(open(file_name, "rb"))
                file.name = str(r['id_photo']) + ".jpg"

                p = Picture(
                        name=str(r['id_photo']) + ".jpg",
                        owner=user,
                        is_moderated=True,
                        is_folder=False,
                        mime_type="image/jpeg",
                        parent=parent,
                        file=file,
                        )
                if r['date_prise_vue']:
                    p.date = r['date_prise_vue'].replace(tzinfo=timezone('Europe/Paris'))
                else:
                    p.date = r['date_ajout_ph'].replace(tzinfo=timezone('Europe/Paris'))
                for f in p._meta.local_fields:
                    if f.name == "date":
                        f.auto_now = False
                p.generate_thumbnails()
                p.save()
                db2 = MySQLdb.connect(**settings.OLD_MYSQL_INFOS)
                cur2 = db2.cursor(MySQLdb.cursors.SSDictCursor)
                cur2.execute("""
                SELECT *
                FROM sas_personnes_photos
                WHERE id_photo = %s
                """, (r['id_photo'], ))
                for r2 in cur2:
                    try:
                        u = User.objects.filter(id=r2['id_utilisateur']).first()
                        if u:
                            PeoplePictureRelation(user=u, picture=p).save()
                    except:
                        print("Fail to associate user %d to picture %d" % (r2['id_utilisateur'], p.id))
                has_result = True
            except Exception as e:
                print("FAIL to migrate Picture: %s" % (repr(e)))
        cur.close()
        print("Chunk %d migrated at %s" % (chunk, str(datetime.datetime.now())))
        print("Running time: %s" % (datetime.datetime.now()-start))
        chunk += 1
        finished = not has_result
    print("SAS migrated at %s" % datetime.datetime.now())
    print("Running time: %s" % (datetime.datetime.now()-start))

    # try:
    #     f = File(open(FILE_ROOT + '/' + str(r['banner']) + ".1", 'rb'))
    # except:
    #     f = None

def reset_sas_moderators():
    cur = db.cursor(MySQLdb.cursors.SSDictCursor)
    cur.execute("""
    SELECT *
    FROM sas_photos
    WHERE id_utilisateur_moderateur IS NOT NULL
    """)
    for r in cur:
        try:
            name = str(r['id_photo']) + '.jpg'
            pict = SithFile.objects.filter(name__icontains=name, is_in_sas=True).first()
            user = User.objects.filter(id=r['id_utilisateur_moderateur']).first()
            if pict and user:
                pict.moderator = user
                pict.save()
            else:
                print("No pict %s (%s) or user %s (%s)" %(pict, name, user, r['id_utilisateur_moderateur']))
        except Exception as e:
            print(repr(e))

def main():
    print("Start at %s" % start)
    # Core
    # migrate_core()
    # Club
    # migrate_club()
    # Subscriptions
    # migrate_subscriptions()
    # Counters
    # migrate_counter()
    # check_accounts()
    # Accounting
    # migrate_accounting()
    # migrate_godfathers()
    # migrate_etickets()
    # reset_index('core', 'club', 'subscription', 'accounting', 'eboutic', 'launderette', 'counter')
    # migrate_sas()
    # reset_index('core', 'sas')
    reset_sas_moderators()
    end = datetime.datetime.now()
    print("End at %s" % end)
    print("Running time: %s" % (end-start))

if __name__ == "__main__":
    main()
