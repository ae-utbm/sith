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
