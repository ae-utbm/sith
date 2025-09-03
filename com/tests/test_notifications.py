from datetime import timedelta

import pytest
from django.conf import settings
from django.utils.timezone import now
from model_bakery import baker

from com.models import News, NewsDate
from core.baker_recipes import subscriber_user
from core.models import Group, Notification, User


@pytest.mark.django_db
def test_notification_created():
    # this news is unpublished, but is set in the past
    # it shouldn't be taken into account when counting the number
    # of news that are to be moderated
    past_news = baker.make(News, is_published=False)
    baker.make(NewsDate, news=past_news, start_date=now() - timedelta(days=1))
    com_admin_group = Group.objects.get(pk=settings.SITH_GROUP_COM_ADMIN_ID)
    com_admin_group.users.all().delete()
    Notification.objects.all().delete()
    com_admin = baker.make(User, groups=[com_admin_group])
    for i in range(2):
        # news notifications are permanent, so the notification created
        # during the first iteration should be reused during the second one.
        baker.make(News, is_published=False)
        notifications = list(Notification.objects.all())
        assert len(notifications) == 1
        assert notifications[0].user == com_admin
        assert notifications[0].type == "NEWS_MODERATION"
        assert notifications[0].param == str(i + 1)


@pytest.mark.django_db
def test_notification_edited_when_moderating_news():
    com_admin_group = Group.objects.get(pk=settings.SITH_GROUP_COM_ADMIN_ID)
    com_admins = subscriber_user.make(_quantity=3)
    com_admin_group.users.set(com_admins)
    Notification.objects.all().delete()
    news = baker.make(News, is_published=False)
    assert Notification.objects.count() == 3
    assert Notification.objects.filter(viewed=False).count() == 3

    news.is_published = True
    news.moderator = com_admins[0]
    news.save()
    # when the news is moderated, the notification should be marked as read
    # for all admins
    assert Notification.objects.count() == 3
    assert Notification.objects.filter(viewed=False).count() == 0
