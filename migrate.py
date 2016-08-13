import MySQLdb
import os
import django
import random

os.environ["DJANGO_SETTINGS_MODULE"] = "sith.settings"
django.setup()

from core.models import User, SithFile
from django.db import IntegrityError
from django.conf import settings

PROFILE_ROOT = "/data/matmatronch/"

db = MySQLdb.connect(
        host="ae-db",
        user="taiste_rw",
        passwd=input("password: "),
        db="ae2-taiste",
        charset='utf8',
        use_unicode=True)
c = db.cursor(MySQLdb.cursors.DictCursor)
c.execute("""
SELECT *
FROM utilisateurs utl
JOIN utl_etu ue
ON ue.id_utilisateur = utl.id_utilisateur
JOIN utl_etu_utbm ueu
ON ueu.id_utilisateur = utl.id_utilisateur
JOIN utl_extra uxtra
ON uxtra.id_utilisateur = utl.id_utilisateur
JOIN loc_ville ville
ON utl.id_ville = ville.id_ville
WHERE utl.id_utilisateur > 9000
""")
User.objects.filter(id__gt=0).delete()
print("Users deleted")
# guy = c.fetchone()
# for k,v in sorted(guy.items()):
#     print("%40s | %40s" % (k, v))

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

def to_unicode(s):
    if s:
        return bytes(s, 'cp1252', errors="replace").decode('utf-8', errors='replace')
    return ""

def get_random_free_email():
    id = random.randrange(4000)
    email = "no_email_%s@git.an" % random.randrange(4000, 40000)
    while User.objects.filter(email=email).exists():
        email = "no_email_%s@git.an" % random.randrange(4000, 40000)
    return email

for u in c.fetchall():
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
        )
        new.generate_username()
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

from os import listdir
from django.core.files import File

profile = SithFile.objects.filter(parent=None, name="profiles").first()
for filename in listdir(PROFILE_ROOT):
    if filename.split('.')[-2] != "mini":
        try:
            uid = filename.split('.')[0].split('-')[0]
            user = User.objects.filter(id=int(uid)).first()
            if user:
                f = File(open(PROFILE_ROOT + '/' + filename, 'rb'))
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

#     profile_pict = models.OneToOneField('SithFile', related_name='profile_of', verbose_name=_("profile"), null=True, blank=True)
#     avatar_pict = models.OneToOneField('SithFile', related_name='avatar_of', verbose_name=_("avatar"), null=True, blank=True)
#     scrub_pict = models.OneToOneField('SithFile', related_name='scrub_of', verbose_name=_("scrub"), null=True, blank=True)
