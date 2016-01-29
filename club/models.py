from django.db import models
from django.core import validators
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

from core.models import User

# Create your models here.

class Club(models.Model):
    """
    The Club class, made as a tree to allow nice tidy organization
    """
    name = models.CharField(_('name'), max_length=30)
    parent = models.ForeignKey('Club', related_name='children', null=True, blank=True)
    unix_name = models.CharField(_('unix name'), max_length=30, unique=True,
            validators=[
                validators.RegexValidator(
                    r'^[a-z0-9][a-z0-9._-]*[a-z0-9]$',
                    _('Enter a valid unix name. This value may contain only '
                        'letters, numbers ./-/_ characters.')
                    ),
                ],
            error_messages={
                'unique': _("A club with that unix name already exists."),
                },
            )
    address = models.CharField(_('address'), max_length=254)
    # email = models.EmailField(_('email address'), unique=True) # This should, and will be generated automatically

    def check_loop(self):
        """Raise a validation error when a loop is found within the parent list"""
        objs = []
        cur = self
        while cur.parent is not None:
            if cur in objs:
                raise ValidationError(_('You can not make loops in clubs'))
            objs.append(cur)
            cur = cur.parent

    def clean(self):
        self.check_loop()

    def __str__(self):
        return self.name

class Membership(models.Model):
    """
    The Membership class makes the connection between User and Clubs

    Both Users and Clubs can have many Membership objects:
       - a user can be a member of many clubs at a time
       - a club can have many members at a time too

    A User is currently member of all the Clubs where its Membership has an end_date set to null/None.
    Otherwise, it's a past membership kept because it can be very useful to see who was in which Club in the past.
    """
    user = models.ForeignKey(User, related_name="membership", null=False, blank=False)
    club = models.ForeignKey(Club, related_name="members", null=False, blank=False)
    start_date = models.DateField(_('start date'), auto_now=True)
    end_date = models.DateField(_('end date'), null=True, blank=True)
    role = models.IntegerField(_('role'), choices=sorted(settings.CLUB_ROLES.items()),
            default=sorted(settings.CLUB_ROLES.items())[0][0])
    description = models.CharField(_('description'), max_length=30, null=False, blank=True)

    def clean(self):
        if Membership.objects.filter(user=self.user).filter(club=self.club).filter(end_date=None).exclude(pk=self.pk).exists():
            raise ValidationError(_('User is already member of that club'))

    def __str__(self):
        return self.club.name+' - '+self.user.username+' - '+settings.CLUB_ROLES[self.role]+str(
                " - "+str(_('past member')) if self.end_date is not None else ""
                )



