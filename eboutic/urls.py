#
# Copyright 2016,2017, 2022
# - Skia <skia@libskia.so>
# - Maréchal <thgirod@hotmail.com>
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

from django.urls import path, register_converter

from core.converters import ResultConverter
from eboutic.views import (
    BillingInfoFormFragment,
    EbouticCheckout,
    EbouticMainView,
    EbouticPayWithSith,
    EtransactionAutoAnswer,
    payment_result,
)

register_converter(ResultConverter, "res")

urlpatterns = [
    # Subscription views
    path("", EbouticMainView.as_view(), name="main"),
    path("checkout/<int:basket_id>", EbouticCheckout.as_view(), name="checkout"),
    path("billing-infos/", BillingInfoFormFragment.as_view(), name="billing_infos"),
    path(
        "pay/sith/<int:basket_id>", EbouticPayWithSith.as_view(), name="pay_with_sith"
    ),
    path("pay/<res:result>/", payment_result, name="payment_result"),
    path(
        "et_autoanswer",
        EtransactionAutoAnswer.as_view(),
        name="etransation_autoanswer",
    ),
]
