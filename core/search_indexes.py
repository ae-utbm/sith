# -*- coding:utf-8 -*
#
# Copyright 2016,2017
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
# this program; if not, write to the Free Sofware Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.
#
#

from django.db import models

from haystack import indexes, signals

from core.models import User
from forum.models import ForumMessage, ForumMessageMeta


class UserIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    auto = indexes.EdgeNgramField(use_template=True)

    def get_model(self):
        return User

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()

    def get_updated_field(self):
        return "last_update"

    def prepare_auto(self, obj):
        return self.prepared_data["auto"].strip()


class IndexSignalProcessor(signals.BaseSignalProcessor):
    def setup(self):
        # Listen only to the ``User`` model.
        models.signals.post_save.connect(self.handle_save, sender=User)
        models.signals.post_delete.connect(self.handle_delete, sender=User)

        # Listen only to the ``ForumMessage`` model.
        models.signals.post_save.connect(self.handle_save, sender=ForumMessageMeta)
        models.signals.post_delete.connect(self.handle_delete, sender=ForumMessage)

        # Listen to the ``ForumMessageMeta`` model pretending it's a ``ForumMessage``.
        models.signals.post_save.connect(
            self.handle_forum_message_meta_save, sender=ForumMessageMeta
        )
        models.signals.post_delete.connect(
            self.handle_forum_message_meta_delete, sender=ForumMessageMeta
        )

    def teardown(self):
        # Disconnect only for the ``User`` model.
        models.signals.post_save.disconnect(self.handle_save, sender=User)
        models.signals.post_delete.disconnect(self.handle_delete, sender=User)

        # Disconnect only to the ``ForumMessage`` model.
        models.signals.post_save.disconnect(self.handle_save, sender=ForumMessage)
        models.signals.post_delete.disconnect(self.handle_delete, sender=ForumMessage)

        # Disconnect to the ``ForumMessageMeta`` model pretending it's a ``ForumMessage``.
        models.signals.post_save.disconnect(
            self.handle_forum_message_meta_save, sender=ForumMessageMeta
        )
        models.signals.post_delete.disconnect(
            self.handle_forum_message_meta_delete, sender=ForumMessageMeta
        )

    def handle_forum_message_meta_save(self, sender, instance, **kwargs):
        super(IndexSignalProcessor, self).handle_save(
            ForumMessage, instance.message, **kwargs
        )

    def handle_forum_message_meta_delete(self, sender, instance, **kwargs):
        super(IndexSignalProcessor, self).handle_delete(
            ForumMessage, instance.message, **kwargs
        )


class BigCharFieldIndex(indexes.CharField):
    """
    Workaround to avoid xapian.InvalidArgument: Term too long (> 245)
    See https://groups.google.com/forum/#!topic/django-haystack/hRJKcPNPXqw/discussion
    """

    def prepare(self, term):
        return bytes(super(BigCharFieldIndex, self).prepare(term), "utf-8")[
            :245
        ].decode("utf-8", errors="ignore")


class ForumMessageIndex(indexes.SearchIndex, indexes.Indexable):
    text = BigCharFieldIndex(document=True, use_template=True)
    auto = indexes.EdgeNgramField(use_template=True)
    date = indexes.DateTimeField(model_attr="date")

    def get_model(self):
        return ForumMessage
