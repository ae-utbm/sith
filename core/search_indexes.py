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

from core.models import User
from forum.models import ForumMessage, ForumMessageMeta


class UserIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    auto = indexes.EdgeNgramField(use_template=True)
    last_update = indexes.DateTimeField(model_attr="last_update")

    def get_model(self):
        return User

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()

    def get_updated_field(self):
        return "last_update"

    def prepare_auto(self, obj):
        return self.prepared_data["auto"].strip()[:245]


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
