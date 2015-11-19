from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.utils.translation import ugettext_lazy as _
from django.core import validators
from django.utils import timezone

class User(AbstractBaseUser, PermissionsMixin):
    """
    Defines the base user class, useable in every app

    This is almost the same as the auth module AbstractUser since it inherits from it,
    but some fields are required, and the username is generated automatically with the
    name of the user (see generate_username()).

    Added field: nick_name
    Required fields: email, first_name, last_name, date_of_birth
    """
    username = models.CharField(
        _('username'),
        max_length=254,
        unique=True,
        help_text=_('Required. 254 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[
            validators.RegexValidator(
                r'^[\w.@+-]+$',
                _('Enter a valid username. This value may contain only '
                  'letters, numbers ' 'and @/./+/-/_ characters.')
            ),
        ],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    first_name = models.CharField(_('first name'), max_length=30)
    last_name = models.CharField(_('last name'), max_length=30)
    email = models.EmailField(_('email address'), unique=True)
    date_of_birth = models.DateTimeField(_('date of birth'), default="1970-01-01T00:00:00+01:00")
    nick_name = models.CharField(max_length=30, blank=True)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.username

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        "Returns the short name for the user."
        return self.first_name

    def get_display_name(self):
        """
        Returns the display name of the user.
        A nickname if possible, otherwise, the full name
        """
        if self.nick_name != "":
            return self.nick_name
        return self.get_full_name()

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def generate_username(self):
        """
        Generates a unique username based on the first and last names.
        For example: Guy Carlier gives gcarlier, and gcarlier1 if the first one exists
        Returns the generated username
        """
        user_name = str(self.first_name[0]+self.last_name).lower()
        un_set = [u.username for u in User.objects.all()]
        if user_name in un_set:
            i = 1
            while user_name+str(i) in un_set:
                i += 1
            user_name += str(i)
        self.username = user_name
        return user_name

class Page(models.Model):
    name = models.CharField(_('page name'), max_length=30, blank=False)
    full_name = models.CharField(_("full name"), max_length=255, blank=False)
    content = models.TextField(_("page content"), blank=True)
    revision = models.PositiveIntegerField(_("current revision"), default=1)
    is_locked = models.BooleanField(_("page mutex"), default=False)

    class Meta:
        permissions = (
            ("can_edit", "Can edit the page"),
            ("can_view", "Can view the page"),
        )

    def __str__(self):
        return self.full_name

