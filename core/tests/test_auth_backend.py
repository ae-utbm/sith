import pytest
from django.contrib.auth.models import Permission
from model_bakery import baker

from core.models import Group, User


@pytest.mark.django_db
def test_with_perm():
    """Test that `SithModelBackend.with_perm` works as intended."""
    perms = baker.make(Permission, _quantity=4)
    groups = baker.make(Group, _quantity=2)
    groups[0].permissions.set(perms[0:2])
    groups[1].permissions.set(perms[2:4])
    users = [
        baker.make(User),
        baker.make(User, groups=[groups[0]]),
        baker.make(User, groups=[groups[1]]),
        baker.make(User, user_permissions=[perms[0]]),
        baker.make(User, user_permissions=[perms[2]]),
        baker.make(User, groups=[groups[1]], user_permissions=[perms[0]]),
    ]

    expected = [users[1], users[3], users[5]]
    assert list(User.objects.with_perm(perms[0])) == expected
    str_repr = f"{perms[0].content_type.app_label}.{perms[0].codename}"
    assert list(User.objects.with_perm(str_repr)) == expected
