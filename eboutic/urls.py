# -*- coding:utf-8 -*-
#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
# All contributors are listed in the CONTRIBUTORS file.
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the whole source code at https://github.com/ae-utbm/sith3
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
# PREVIOUSLY LICENSED UNDER THE MIT LICENSE,
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE.old
# OR WITHIN THE LOCAL FILE "LICENSE.old"
#

from django.urls import path, register_converter

from eboutic.converters import PaymentResultConverter
from eboutic.views import *

register_converter(PaymentResultConverter, "res")

urlpatterns = [
    # Subscription views
    path("", eboutic_main, name="main"),
    path("command/", EbouticCommand.as_view(), name="command"),
    path("pay/sith/", pay_with_sith, name="pay_with_sith"),
    path("pay/<res:result>/", payment_result, name="payment_result"),
    path("et_data/", e_transaction_data, name="et_data"),
    path(
        "et_autoanswer",
        EtransactionAutoAnswer.as_view(),
        name="etransation_autoanswer",
    ),
]
