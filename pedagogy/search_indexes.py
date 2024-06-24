# -*- coding:utf-8 -*
#
# Copyright 2019
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
# this program; if not, write to the Free Sofware Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.
#
#

from django.db import models
from haystack import indexes, signals

from core.search_indexes import BigCharFieldIndex
from pedagogy.models import UV


class IndexSignalProcessor(signals.BaseSignalProcessor):
    """
    Auto update index on CRUD operations
    """

    def setup(self):
        # Listen only to the ``UV`` model.
        models.signals.post_save.connect(self.handle_save, sender=UV)
        models.signals.post_delete.connect(self.handle_delete, sender=UV)

    def teardown(self):
        # Disconnect only to the ``UV`` model.
        models.signals.post_save.disconnect(self.handle_save, sender=UV)
        models.signals.post_delete.disconnect(self.handle_delete, sender=UV)


class UVIndex(indexes.SearchIndex, indexes.Indexable):
    """
    Indexer class for UVs
    """

    text = BigCharFieldIndex(document=True, use_template=True)
    auto = indexes.EdgeNgramField(use_template=True)

    def get_model(self):
        return UV
