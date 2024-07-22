#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the source code of the website at https://github.com/ae-utbm/sith3
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
#

import pytest
from django.conf import settings
from django.test import Client
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from core.models import User
from forum.models import Forum, ForumMessage, ForumTopic


@pytest.mark.django_db
class TestTopicCreation:
    def test_topic_creation_ok(self, client: Client):
        user: User = User.objects.get(username="root")
        forum = Forum.objects.get(name="AE")
        client.force_login(user)
        payload = {
            "title": "Hello IT.",
            "message": "Have you tried turning it off and on again ?",
            settings.HONEYPOT_FIELD_NAME_FORUM: settings.HONEYPOT_VALUE,
        }
        assert not ForumTopic.objects.filter(_title=payload["title"]).exists()
        response = client.post(reverse("forum:new_topic", args=str(forum.id)), payload)
        assertRedirects(
            response,
            expected_url=reverse(
                "forum:view_message",
                args=str(ForumMessage.objects.order_by("date").last().id),
            ),  # Get the last created message id
            target_status_code=302,
        )
        topic = ForumTopic.objects.filter(_title=payload["title"]).first()
        assert topic
        assert topic.last_message.message == payload["message"]

    def test_topic_creation_honeypot_fail(self, client: Client):
        user: User = User.objects.get(username="root")
        forum = Forum.objects.get(name="AE")
        client.force_login(user)
        payload = {
            "title": "You shall",
            "message": "Not pass !",
            settings.HONEYPOT_FIELD_NAME_FORUM: settings.HONEYPOT_VALUE + "random",
        }
        assert not ForumTopic.objects.filter(_title=payload["title"]).exists()
        response = client.post(reverse("forum:new_topic", args=str(forum.id)), payload)
        assert response.status_code == 200
        assert not ForumTopic.objects.filter(_title=payload["title"]).exists()

    def test_topic_creation_fail(self, client: Client):
        user: User = User.objects.get(username="krophil")
        forum = Forum.objects.get(name="AE")
        client.force_login(user)
        payload = {
            "title": "You shall",
            "message": "Not pass !",
            settings.HONEYPOT_FIELD_NAME_FORUM: settings.HONEYPOT_VALUE,
        }
        assert not ForumTopic.objects.filter(_title=payload["title"]).exists()
        response = client.post(reverse("forum:new_topic", args=str(forum.id)), payload)
        assert response.status_code == 403
        assert not ForumTopic.objects.filter(_title=payload["title"]).exists()
