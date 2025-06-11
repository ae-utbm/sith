import pytest
from django.conf import settings
from model_bakery import baker

from com.models import News
from core.models import Group, Notification, User


@pytest.mark.django_db
def test_notification_created():
    com_admin_group = Group.objects.get(pk=settings.SITH_GROUP_COM_ADMIN_ID)
    com_admin_group.users.all().delete()
    Notification.objects.all().delete()
    com_admin = baker.make(User, groups=[com_admin_group])
    for i in range(2):
        # news notifications are permanent, so the notification created
        # during the first iteration should be reused during the second one.
        baker.make(News)
        notifications = list(Notification.objects.all())
        assert len(notifications) == 1
        assert notifications[0].user == com_admin
        assert notifications[0].type == "NEWS_MODERATION"
        assert notifications[0].param == str(i + 1)
