# -*- coding:utf-8 -*
#
# Copyright 2022
# - Maréchal <thgirod@hotmail.com
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


class PaymentResultConverter:
    """
    Converter used for url mapping of the ``eboutic.views.payment_result``
    view.
    It's meant to build an url that can match
    either ``/eboutic/pay/success/`` or ``/eboutic/pay/failure/``
    but nothing else.
    """

    regex = "(success|failure)"

    def to_python(self, value):
        return str(value)

    def to_url(self, value):
        return str(value)
