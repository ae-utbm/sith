#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the source code of the website at https://github.com/ae-utbm/sith
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
#

from django.contrib import admin

from accounting.models import *

admin.site.register(BankAccount)
admin.site.register(ClubAccount)
admin.site.register(GeneralJournal)
admin.site.register(AccountingType)
admin.site.register(SimplifiedAccountingType)
admin.site.register(Operation)
admin.site.register(Label)
admin.site.register(Company)
