#
# Copyright 2016,2017,2024
# - Skia <skia@libskia.so>
# - Sli <antoine@bartuccio.fr>
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
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.
#
#

"""Django settings for sith project.

Generated by 'django-admin startproject' using Django 1.8.6.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

import binascii
import os
import sys
from datetime import timedelta
from pathlib import Path

import sentry_sdk
from dateutil.relativedelta import relativedelta
from django.utils.translation import gettext_lazy as _
from environs import Env
from sentry_sdk.integrations.django import DjangoIntegration

from .honeypot import custom_honeypot_error

env = Env()
env.read_env()


@env.parser_for("optional_file")
def optional_file_parser(value: str) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if not path.is_file():
        return None
    return path


BASE_DIR = Path(__file__).parent.parent.resolve()

# Composer settings
PROCFILE_STATIC = env.optional_file("PROCFILE_STATIC", None)
PROCFILE_SERVICE = env.optional_file("PROCFILE_SERVICE", None)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("SITH_DEBUG", default=False)
TESTING = "pytest" in sys.modules
INTERNAL_IPS = ["127.0.0.1"]

HTTPS = env.bool("HTTPS", default=True)

# force csrf tokens and cookies to be secure when in https
CSRF_COOKIE_SECURE = HTTPS
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
SESSION_COOKIE_SECURE = HTTPS
X_FRAME_OPTIONS = "SAMEORIGIN"

ALLOWED_HOSTS = ["*"]

# Application definition

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

SITE_ID = 4000

INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "staticfiles",
    "django.contrib.sites",
    "honeypot",
    "django_jinja",
    "ninja_extra",
    "haystack",
    "captcha",
    "core",
    "club",
    "subscription",
    "accounting",
    "counter",
    "eboutic",
    "launderette",
    "rootplace",
    "sas",
    "com",
    "election",
    "forum",
    "trombi",
    "matmat",
    "pedagogy",
    "galaxy",
    "antispam",
)

MIDDLEWARE = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "core.middleware.AuthenticationMiddleware",
    "core.middleware.SignalRequestMiddleware",
)

ROOT_URLCONF = "sith.urls"

TEMPLATES = [
    {
        "NAME": "jinja2",
        "BACKEND": "django_jinja.backend.Jinja2",
        "APP_DIRS": True,
        "OPTIONS": {
            "match_extension": ".jinja",
            "app_dirname": "templates",
            "newstyle_gettext": True,
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
            ],
            "extensions": [
                "jinja2.ext.do",
                "jinja2.ext.loopcontrols",
                "jinja2.ext.i18n",
                "django_jinja.builtins.extensions.CsrfExtension",
                "django_jinja.builtins.extensions.CacheExtension",
                "django_jinja.builtins.extensions.TimezoneExtension",
                "django_jinja.builtins.extensions.UrlsExtension",
                "django_jinja.builtins.extensions.StaticFilesExtension",
                "django_jinja.builtins.extensions.DjangoFiltersExtension",
                "core.templatetags.extensions.HoneypotExtension",
            ],
            "filters": {
                "markdown": "core.templatetags.renderer.markdown",
                "phonenumber": "core.templatetags.renderer.phonenumber",
                "truncate_time": "core.templatetags.renderer.truncate_time",
                "format_timedelta": "core.templatetags.renderer.format_timedelta",
                "add_attr": "core.templatetags.renderer.add_attr",
            },
            "globals": {
                "can_edit_prop": "core.auth.mixins.can_edit_prop",
                "can_edit": "core.auth.mixins.can_edit",
                "can_view": "core.auth.mixins.can_view",
                "settings": "sith.settings",
                "Launderette": "launderette.models.Launderette",
                "Counter": "counter.models.Counter",
                "timezone": "django.utils.timezone",
                "get_sith": "com.views.sith",
                "get_language": "django.utils.translation.get_language",
                "timedelta": "datetime.timedelta",
            },
            "bytecode_cache": {
                "name": "default",
                "backend": "django_jinja.cache.BytecodeCache",
                "enabled": False,
            },
            "autoescape": True,
            "auto_reload": True,
            "translation_engine": "django.utils.translation",
        },
    },
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    },
]
FORM_RENDERER = "django.forms.renderers.DjangoDivFormRenderer"

HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "xapian_backend.XapianEngine",
        "PATH": os.path.join(os.path.dirname(__file__), "search_indexes", "xapian"),
        "INCLUDE_SPELLING": True,
    }
}

HAYSTACK_SIGNAL_PROCESSOR = "core.search_indexes.IndexSignalProcessor"

SASS_PRECISION = 8

WSGI_APPLICATION = "sith.wsgi.application"

# Database

DATABASES = {
    "default": env.dj_db_url("DATABASE_URL", conn_max_age=None, conn_health_checks=True)
}

CACHES = {"default": env.dj_cache_url("CACHE_URL")}

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "handlers": {
        "log_to_stdout": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "dump_mail_file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "account_dump_mail.log",
            "formatter": "simple",
        },
    },
    "loggers": {
        "main": {
            "handlers": ["log_to_stdout"],
            "level": "INFO",
            "propagate": True,
        },
        "account_dump_mail": {"handlers": ["dump_mail_file", "log_to_stdout"]},
    },
}

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = "fr-FR"

LANGUAGES = [("en", _("English")), ("fr", _("French"))]

TIME_ZONE = "Europe/Paris"

USE_I18N = True

USE_TZ = True

LOCALE_PATHS = [BASE_DIR / "locale"]

PHONENUMBER_DEFAULT_REGION = "FR"

# Medias
MEDIA_URL = "/data/"
MEDIA_ROOT = env.path("MEDIA_ROOT", default=BASE_DIR / "data")

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = env.path("STATIC_ROOT", default=BASE_DIR / "static")

# Static files finders which allow to see static folder in all apps
STATICFILES_FINDERS = [
    "staticfiles.finders.GeneratedFilesFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "staticfiles.storage.ManifestPostProcessingStorage",
    },
}

# Auth configuration
AUTH_USER_MODEL = "core.User"
AUTH_ANONYMOUS_MODEL = "core.models.AnonymousUser"
AUTHENTICATION_BACKENDS = ["core.auth.backends.SithModelBackend"]
LOGIN_URL = "/login/"
LOGOUT_URL = "/logout/"
LOGIN_REDIRECT_URL = "/"
DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL", default="bibou@git.an")
SITH_COM_EMAIL = env.str("SITH_COM_EMAIL", default="bibou_com@git.an")

# Those values are to be changed in production to be more effective
HONEYPOT_FIELD_NAME = env.str("HONEYPOT_FIELD_NAME", default="body2")
HONEYPOT_VALUE = env.str("HONEYPOT_VALUE", default="content")
HONEYPOT_RESPONDER = custom_honeypot_error  # Make honeypot errors less suspicious
HONEYPOT_FIELD_NAME_FORUM = env.str(
    "HONEYPOT_FIELD_NAME_FORUM", default="message2"
)  # Only used on forum

# Email
EMAIL_BACKEND = env.str(
    "EMAIL_BACKEND", default="django.core.mail.backends.dummy.EmailBackend"
)
EMAIL_HOST = env.str("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=25)

# Below this line, only Sith-specific variables are defined

SITH_URL = env.str("SITH_URL", default="127.0.0.1:8000")
SITH_NAME = env.str("SITH_NAME", default="AE UTBM")
SITH_TWITTER = "@ae_utbm"

# AE configuration
SITH_MAIN_CLUB_ID = env.int("SITH_MAIN_CLUB_ID", default=1)
SITH_PDF_CLUB_ID = env.int("SITH_PDF_CLUB_ID", default=2)
SITH_LAUNDERETTE_CLUB_ID = env.int("SITH_LAUNDERETTE_CLUB_ID", default=84)

# Main root for club pages
SITH_CLUB_ROOT_PAGE = "clubs"

# Define the date in the year serving as
# reference for the subscriptions calendar (month, day)
SITH_SEMESTER_START_AUTUMN = (8, 15)  # 15 August
SITH_SEMESTER_START_SPRING = (2, 15)  # 15 February

# Used to determine the valid promos
SITH_SCHOOL_START_YEAR = 1999

# id of the Root account
SITH_ROOT_USER_ID = 0

SITH_GROUP_ROOT_ID = env.int("SITH_GROUP_ROOT_ID", default=1)
SITH_GROUP_PUBLIC_ID = env.int("SITH_GROUP_PUBLIC_ID", default=2)
SITH_GROUP_SUBSCRIBERS_ID = env.int("SITH_GROUP_SUBSCRIBERS_ID", default=3)
SITH_GROUP_OLD_SUBSCRIBERS_ID = env.int("SITH_GROUP_OLD_SUBSCRIBERS_ID", default=4)
SITH_GROUP_ACCOUNTING_ADMIN_ID = env.int("SITH_GROUP_ACCOUNTING_ADMIN_ID", default=5)
SITH_GROUP_COM_ADMIN_ID = env.int("SITH_GROUP_COM_ADMIN_ID", default=6)
SITH_GROUP_COUNTER_ADMIN_ID = env.int("SITH_GROUP_COUNTER_ADMIN_ID", default=7)
SITH_GROUP_SAS_ADMIN_ID = env.int("SITH_GROUP_SAS_ADMIN_ID", default=8)
SITH_GROUP_FORUM_ADMIN_ID = env.int("SITH_GROUP_FORUM_ADMIN_ID", default=9)
SITH_GROUP_PEDAGOGY_ADMIN_ID = env.int("SITH_GROUP_PEDAGOGY_ADMIN_ID", default=10)

SITH_GROUP_BANNED_ALCOHOL_ID = env.int("SITH_GROUP_BANNED_ALCOHOL_ID", default=11)
SITH_GROUP_BANNED_COUNTER_ID = env.int("SITH_GROUP_BANNED_COUNTER_ID", default=12)
SITH_GROUP_BANNED_SUBSCRIPTION_ID = env.int(
    "SITH_GROUP_BANNED_SUBSCRIPTION_ID", default=13
)

SITH_CLUB_REFOUND_ID = env.int("SITH_CLUB_REFOUND_ID", default=89)
SITH_COUNTER_REFOUND_ID = env.int("SITH_COUNTER_REFOUND_ID", default=38)
SITH_PRODUCT_REFOUND_ID = env.int("SITH_PRODUCT_REFOUND_ID", default=5)

SITH_COUNTER_ACCOUNT_DUMP_ID = env.int("SITH_COUNTER_ACCOUNT_DUMP_ID", default=39)

# Pages
SITH_CORE_PAGE_SYNTAX = "Aide_sur_la_syntaxe"

# Forum

SITH_FORUM_PAGE_LENGTH = 30

# SAS variables
SITH_SAS_ROOT_DIR_ID = env.int("SITH_SAS_ROOT_DIR_ID", default=4)
SITH_SAS_IMAGES_PER_PAGE = 60

SITH_BOARD_SUFFIX = "-bureau"
SITH_MEMBER_SUFFIX = "-membres"

SITH_PROFILE_DEPARTMENTS = [
    ("TC", _("TC")),
    ("IMSI", _("IMSI")),
    ("IMAP", _("IMAP")),
    ("INFO", _("INFO")),
    ("GI", _("GI")),
    ("E", _("E")),
    ("EE", _("EE")),
    ("GESC", _("GESC")),
    ("GMC", _("GMC")),
    ("MC", _("MC")),
    ("EDIM", _("EDIM")),
    ("HUMA", _("Humanities")),
    ("NA", _("N/A")),
]

SITH_ACCOUNTING_PAYMENT_METHOD = [
    ("CHECK", _("Check")),
    ("CASH", _("Cash")),
    ("TRANSFERT", _("Transfert")),
    ("CARD", _("Credit card")),
]

SITH_SUBSCRIPTION_PAYMENT_METHOD = [
    ("CHECK", _("Check")),
    ("CARD", _("Credit card")),
    ("CASH", _("Cash")),
    ("EBOUTIC", _("Eboutic")),
    ("OTHER", _("Other")),
]

SITH_SUBSCRIPTION_LOCATIONS = [
    ("BELFORT", _("Belfort")),
    ("SEVENANS", _("Sevenans")),
    ("MONTBELIARD", _("Montbéliard")),
    ("EBOUTIC", _("Eboutic")),
]

SITH_COUNTER_BARS = [(1, "MDE"), (2, "Foyer"), (35, "La Gommette")]

SITH_COUNTER_BANK = [
    ("OTHER", "Autre"),
    ("SOCIETE-GENERALE", "Société générale"),
    ("BANQUE-POPULAIRE", "Banque populaire"),
    ("BNP", "BNP"),
    ("CAISSE-EPARGNE", "Caisse d'épargne"),
    ("CIC", "CIC"),
    ("CREDIT-AGRICOLE", "Crédit Agricole"),
    ("CREDIT-MUTUEL", "Credit Mutuel"),
    ("CREDIT-LYONNAIS", "Credit Lyonnais"),
    ("LA-POSTE", "La Poste"),
]

SITH_PEDAGOGY_UV_TYPE = [
    ("FREE", _("Free")),
    ("CS", _("CS")),
    ("TM", _("TM")),
    ("OM", _("OM")),
    ("QC", _("QC")),
    ("EC", _("EC")),
    ("RN", _("RN")),
    ("ST", _("ST")),
    ("EXT", _("EXT")),
]

SITH_PEDAGOGY_UV_SEMESTER = [
    ("CLOSED", _("Closed")),
    ("AUTUMN", _("Autumn")),
    ("SPRING", _("Spring")),
    ("AUTUMN_AND_SPRING", _("Autumn and spring")),
]

SITH_PEDAGOGY_UV_LANGUAGE = [
    ("FR", _("French")),
    ("EN", _("English")),
    ("DE", _("German")),
    ("SP", _("Spanish")),
]

SITH_PEDAGOGY_UV_RESULT_GRADE = [
    ("A", _("A")),
    ("B", _("B")),
    ("C", _("C")),
    ("D", _("D")),
    ("E", _("E")),
    ("FX", _("FX")),
    ("F", _("F")),
    ("ABS", _("Abs")),
]

SITH_LOG_OPERATION_TYPE = [
    ("SELLING_DELETION", _("Selling deletion")),
    ("REFILLING_DELETION", _("Refilling deletion")),
]

SITH_PEDAGOGY_UTBM_API = "https://extranet1.utbm.fr/gpedago/api/guide"

SITH_ECOCUP_CONS = env.int("SITH_ECOCUP_CONS", default=1151)

SITH_ECOCUP_DECO = env.int("SITH_ECOCUP_DECO", default=1152)

# The limit is the maximum difference between cons and deco possible for a customer
SITH_ECOCUP_LIMIT = 3

# Defines pagination for cash summary
SITH_COUNTER_CASH_SUMMARY_LENGTH = 50

SITH_ACCOUNT_INACTIVITY_DELTA = relativedelta(years=2)
"""Time before which a user account is considered inactive"""
SITH_ACCOUNT_DUMP_DELTA = timedelta(days=30)
"""timedelta between the warning mail and the actual account dump"""

# Defines which product type is the refilling type,
# and thus increases the account amount
SITH_COUNTER_PRODUCTTYPE_REFILLING = env.int(
    "SITH_COUNTER_PRODUCTTYPE_REFILLING", default=3
)

# Defines which product is the one year subscription
# and which one is the six month subscription
SITH_PRODUCT_SUBSCRIPTION_ONE_SEMESTER = env.int(
    "SITH_PRODUCT_SUBSCRIPTION_ONE_SEMESTER", default=1
)
SITH_PRODUCT_SUBSCRIPTION_TWO_SEMESTERS = env.int(
    "SITH_PRODUCT_SUBSCRIPTION_TWO_SEMESTERS", default=2
)
SITH_PRODUCTTYPE_SUBSCRIPTION = env.int("SITH_PRODUCTTYPE_SUBSCRIPTION", default=2)

# Number of weeks before the end of a subscription when the subscriber can resubscribe
SITH_SUBSCRIPTION_END = 10

# Subscription durations are in semestres
# Be careful, modifying this parameter will need a migration to be applied
SITH_SUBSCRIPTIONS = {
    "un-semestre": {"name": _("One semester"), "price": 20, "duration": 1},
    "deux-semestres": {"name": _("Two semesters"), "price": 35, "duration": 2},
    "cursus-tronc-commun": {
        "name": _("Common core cursus"),
        "price": 60,
        "duration": 4,
    },
    "cursus-branche": {"name": _("Branch cursus"), "price": 60, "duration": 6},
    "cursus-alternant": {"name": _("Alternating cursus"), "price": 30, "duration": 6},
    "membre-honoraire": {"name": _("Honorary member"), "price": 0, "duration": 666},
    "assidu": {"name": _("Assidu member"), "price": 0, "duration": 2},
    "amicale/doceo": {"name": _("Amicale/DOCEO member"), "price": 0, "duration": 2},
    "reseau-ut": {"name": _("UT network member"), "price": 0, "duration": 1},
    "crous": {"name": _("CROUS member"), "price": 0, "duration": 2},
    "sbarro/esta": {"name": _("Sbarro/ESTA member"), "price": 15, "duration": 2},
    "un-semestre-welcome": {
        "name": _("One semester Welcome Week"),
        "price": 0,
        "duration": 1,
    },
    "un-mois-essai": {"name": _("One month for free"), "price": 0, "duration": 0.166},
    "deux-mois-essai": {"name": _("Two months for free"), "price": 0, "duration": 0.33},
    "benevoles-euroks": {"name": _("Eurok's volunteer"), "price": 5, "duration": 0.1},
    "six-semaines-essai": {
        "name": _("Six weeks for free"),
        "price": 0,
        "duration": 0.23,
    },
    "un-jour": {"name": _("One day"), "price": 0, "duration": 0.00555333},
    "membre-staff-ga": {"name": _("GA staff member"), "price": 1, "duration": 0.076},
    # Discount subscriptions
    "un-semestre-reduction": {
        "name": _("One semester (-20%)"),
        "price": 12,
        "duration": 1,
    },
    "deux-semestres-reduction": {
        "name": _("Two semesters (-20%)"),
        "price": 22,
        "duration": 2,
    },
    "cursus-tronc-commun-reduction": {
        "name": _("Common core cursus (-20%)"),
        "price": 36,
        "duration": 4,
    },
    "cursus-branche-reduction": {
        "name": _("Branch cursus (-20%)"),
        "price": 36,
        "duration": 6,
    },
    "cursus-alternant-reduction": {
        "name": _("Alternating cursus (-20%)"),
        "price": 24,
        "duration": 6,
    },
    # CA special offer
    "un-an-offert-CA": {
        "name": _("One year for free(CA offer)"),
        "price": 0,
        "duration": 2,
    },
    # To be completed....
}

SITH_CLUB_ROLES_ID = {
    "President": 10,
    "Vice-President": 9,
    "Treasurer": 7,
    "Communication supervisor": 5,
    "Secretary": 4,
    "IT supervisor": 3,
    "Board member": 2,
    "Active member": 1,
    "Curious": 0,
}

SITH_CLUB_ROLES = {
    10: _("President"),
    9: _("Vice-President"),
    7: _("Treasurer"),
    5: _("Communication supervisor"),
    4: _("Secretary"),
    3: _("IT supervisor"),
    2: _("Board member"),
    1: _("Active member"),
    0: _("Curious"),
}

# This corresponds to the maximum role a user can freely subscribe to
# In this case, SITH_MAXIMUM_FREE_ROLE=1 means that a user can
# set himself as "Membre actif" or "Curieux", but not higher
SITH_MAXIMUM_FREE_ROLE = 1

# Minutes to timeout the logged barmen
SITH_BARMAN_TIMEOUT = 30

# Minutes to delete the last operations
SITH_LAST_OPERATIONS_LIMIT = 10

# ET variables
SITH_EBOUTIC_CB_ENABLED = env.bool("SITH_EBOUTIC_CB_ENABLED", default=True)
SITH_EBOUTIC_ET_URL = env.str(
    "SITH_EBOUTIC_ET_URL",
    default="https://preprod-tpeweb.e-transactions.fr/cgi/MYchoix_pagepaiement.cgi",
)
SITH_EBOUTIC_PBX_SITE = env.str("SITH_EBOUTIC_PBX_SITE", default="1999888")
SITH_EBOUTIC_PBX_RANG = env.str("SITH_EBOUTIC_PBX_RANG", default="32")
SITH_EBOUTIC_PBX_IDENTIFIANT = env.str("SITH_EBOUTIC_PBX_IDENTIFIANT", default="2")
SITH_EBOUTIC_HMAC_KEY = binascii.unhexlify(
    env.str(
        "SITH_EBOUTIC_HMAC_KEY",
        default=(
            "0123456789ABCDEF0123456789ABCDEF"
            "0123456789ABCDEF0123456789ABCDEF"
            "0123456789ABCDEF0123456789ABCDEF"
            "0123456789ABCDEF0123456789ABCDEF"
        ),
    )
)
SITH_EBOUTIC_PUB_KEY = ""
with open(
    env.path("SITH_EBOUTIC_PUB_KEY_PATH", default=BASE_DIR / "sith/et_keys/pubkey.pem")
) as f:
    SITH_EBOUTIC_PUB_KEY = f.read()

# Launderette variables
SITH_LAUNDERETTE_MACHINE_TYPES = [("WASHING", _("Washing")), ("DRYING", _("Drying"))]
SITH_LAUNDERETTE_PRICES = {"WASHING": 1.0, "DRYING": 0.75}

SITH_NOTIFICATIONS = [
    ("POSTER_MODERATION", _("A new poster needs to be moderated")),
    ("MAILING_MODERATION", _("A new mailing list needs to be moderated")),
    (
        "PEDAGOGY_MODERATION",
        _("A new pedagogy comment has been signaled for moderation"),
    ),
    ("NEWS_MODERATION", _("There are %s fresh news to be moderated")),
    ("FILE_MODERATION", _("New files to be moderated")),
    ("SAS_MODERATION", _("There are %s pictures to be moderated in the SAS")),
    ("NEW_PICTURES", _("You've been identified on some pictures")),
    ("REFILLING", _("You just refilled of %s €")),
    ("SELLING", _("You just bought %s")),
    ("GENERIC", _("You have a notification")),
]

# The keys are the notification names as found in SITH_NOTIFICATIONS, and the
# values are the callback function to update the notifs.
# The callback must take the notif object as first and single argument.
SITH_PERMANENT_NOTIFICATIONS = {
    "NEWS_MODERATION": "com.models.news_notification_callback",
    "SAS_MODERATION": "sas.models.sas_notification_callback",
}

SITH_QUICK_NOTIF = {
    "qn_success": _("Success!"),
    "qn_fail": _("Fail!"),
    "qn_weekmail_new_article": _("You successfully posted an article in the Weekmail"),
    "qn_weekmail_article_edit": _("You successfully edited an article in the Weekmail"),
    "qn_weekmail_send_success": _("You successfully sent the Weekmail"),
}

# Mailing related settings

SITH_MAILING_DOMAIN = "utbm.fr"
SITH_MAILING_FETCH_KEY = env.str("SITH_MAILING_FETCH_KEY", default="ILoveMails")

SITH_GIFT_LIST = [("AE Tee-shirt", _("AE tee-shirt"))]

SENTRY_DSN = env.str("SENTRY_DSN", default=None)
SENTRY_ENV = env.str("SENTRY_ENV", default="production")

TOXIC_DOMAINS_PROVIDERS = [
    "https://www.stopforumspam.com/downloads/toxic_domains_whole.txt",
]

if DEBUG:
    INSTALLED_APPS += ("debug_toolbar",)
    MIDDLEWARE = ("debug_toolbar.middleware.DebugToolbarMiddleware", *MIDDLEWARE)
    DEBUG_TOOLBAR_PANELS = [
        "debug_toolbar.panels.versions.VersionsPanel",
        "debug_toolbar.panels.timer.TimerPanel",
        "debug_toolbar.panels.settings.SettingsPanel",
        "debug_toolbar.panels.headers.HeadersPanel",
        "debug_toolbar.panels.request.RequestPanel",
        "debug_toolbar.panels.sql.SQLPanel",
        "debug_toolbar.panels.staticfiles.StaticFilesPanel",
        "sith.toolbar_debug.TemplatesPanel",
        "debug_toolbar.panels.cache.CachePanel",
        "debug_toolbar.panels.signals.SignalsPanel",
        "debug_toolbar.panels.redirects.RedirectsPanel",
    ]
    if not TESTING:
        SENTRY_ENV = "development"  # We can't test if it gets overridden in settings

if TESTING:
    CAPTCHA_TEST_MODE = True
    PASSWORD_HASHERS = [  # not secure, but faster password hasher
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ]
    STORAGES = {  # store files in memory rather than using the hard drive
        "default": {
            "BACKEND": "django.core.files.storage.InMemoryStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

if SENTRY_DSN:
    # Connection to sentry
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=1.0,
        send_default_pii=True,
        environment=SENTRY_ENV,
    )
