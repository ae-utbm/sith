from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager, Group as AuthGroup, GroupManager as AuthGroupManager, AnonymousUser as AuthAnonymousUser
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.core import validators
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.conf import settings
from datetime import datetime, timedelta

import unicodedata

class RealGroupManager(AuthGroupManager):
    def get_queryset(self):
        return super(RealGroupManager, self).get_queryset().filter(is_meta=False)

class MetaGroupManager(AuthGroupManager):
    def get_queryset(self):
        return super(MetaGroupManager, self).get_queryset().filter(is_meta=True)

class Group(AuthGroup):
    is_meta = models.BooleanField(
        _('meta group status'),
        default=False,
        help_text=_('Whether a group is a meta group or not'),
    )
    description = models.CharField(_('description'), max_length=60)
    def get_absolute_url(self):
        """
        This is needed for black magic powered UpdateView's children
        """
        return reverse('core:group_list')

class MetaGroup(Group):
    objects = MetaGroupManager()
    class Meta:
        proxy = True

    def __init__(self, *args, **kwargs):
        super(MetaGroup, self).__init__(*args, **kwargs)
        self.is_meta = True

class RealGroup(Group):
    objects = RealGroupManager()
    class Meta:
        proxy = True

class User(AbstractBaseUser, PermissionsMixin):
    """
    Defines the base user class, useable in every app

    This is almost the same as the auth module AbstractUser since it inherits from it,
    but some fields are required, and the username is generated automatically with the
    name of the user (see generate_username()).

    Added field: nick_name, date_of_birth
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
    date_of_birth = models.DateField(_('date of birth'))
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
    date_joined = models.DateField(_('date joined'), auto_now_add=True)
    owner_group = models.ForeignKey(Group, related_name="owned_user",
                                    default=settings.SITH_GROUPS['root']['id'])
    edit_groups = models.ManyToManyField(Group, related_name="editable_user", blank=True)
    view_groups = models.ManyToManyField(Group, related_name="viewable_user", blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'date_of_birth']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        # Add permissions like this to allow automatic permission validation in is_owner&co
        # model: change_prop_<class_name>
        #        view_<class_name>
        permissions = (
            ("change_prop_user", "Can change the user's properties (groups, ...)"),
            ("view_user", "Can view user's profile"),
        )

    def get_absolute_url(self):
        """
        This is needed for black magic powered UpdateView's children
        """
        return reverse('core:user_profile', kwargs={'user_id': self.pk})

    def __str__(self):
        return self.username

    def to_dict(self):
        return self.__dict__

    def is_in_group(self, group_name):
        """If the user is in the group passed in argument (as string)"""
        if group_name == settings.SITH_GROUPS['public']['name']:
            return True
        if group_name == settings.SITH_MAIN_MEMBERS_GROUP: # We check the subscription if asked
            if 'subscription' in settings.INSTALLED_APPS:
                from subscription import Subscriber
                s = Subscriber.objects.filter(pk=self.pk).first()
                if s is not None and s.is_subscribed():
                    return True
                else:
                    return False
            else:
                return False
        if group_name[-6:] == settings.SITH_BOARD_SUFFIX:
            if 'club' in settings.INSTALLED_APPS:
                from club.models import Club
                name = group_name[:-6]
                c = Club.objects.filter(unix_name=name).first()
                mem = c.get_membership_for(self)
                if mem:
                    return mem.role >= 2
                return False
            else:
                return False
        if group_name == settings.SITH_GROUPS['root']['name'] and self.is_superuser:
            return True
        return self.groups.filter(name=group_name).exists()

    def get_profile(self):
        return {
            "last_name": self.last_name,
            "first_name": self.first_name,
            "nick_name": self.nick_name,
            "date_of_birth": self.date_of_birth,
        }

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
        def remove_accents(data):
            return ''.join(x for x in unicodedata.normalize('NFKD', data) if \
            unicodedata.category(x)[0] == 'L').lower()
        user_name = remove_accents(self.first_name[0]+self.last_name).encode('ascii', 'ignore').decode('utf-8')
        un_set = [u.username for u in User.objects.all()]
        if user_name in un_set:
            i = 1
            while user_name+str(i) in un_set:
                i += 1
            user_name += str(i)
        self.username = user_name
        return user_name

    def is_owner(self, obj):
        """
        Determine if the object is owned by the user
        """
        if hasattr(obj, "is_owned_by") and obj.is_owned_by(self):
            return True
        if hasattr(obj, "owner_group") and self.is_in_group(obj.owner_group.name):
            return False
        if self.is_superuser or self.is_in_group(settings.SITH_GROUPS['root']['name']):
            return True
        return False

    def can_edit(self, obj):
        """
        Determine if the object can be edited by the user
        """
        if self.is_owner(obj):
            return True
        if hasattr(obj, "edit_groups"):
            for g in obj.edit_groups.all():
                if self.is_in_group(g.name):
                    return True
        if isinstance(obj, User) and obj == self:
            return True
        if hasattr(obj, "can_be_edited_by") and obj.can_be_edited_by(self):
            return True
        return False

    def can_view(self, obj):
        """
        Determine if the object can be viewed by the user
        """
        if self.can_edit(obj):
            return True
        if hasattr(obj, "view_groups"):
            for g in obj.view_groups.all():
                if self.is_in_group(g.name):
                    return True
        if hasattr(obj, "can_be_viewed_by") and obj.can_be_viewed_by(self):
            return True
        return False

    def can_be_edited_by(self, user):
        return user.is_in_group(settings.SITH_MAIN_BOARD_GROUP) or user.is_in_group(settings.SITH_GROUPS['root']['name'])


class AnonymousUser(AuthAnonymousUser):
    def __init__(self, request):
        super(AnonymousUser, self).__init__()

    def is_owner(self, obj):
        return False

    def can_edit(self, obj):
        return False

    def can_view(self, obj):
        if hasattr(obj, 'view_groups') and obj.view_groups.filter(pk=settings.SITH_GROUPS['public']['id']).exists():
            return True
        if hasattr(obj, 'can_be_viewed_by') and obj.can_be_viewed_by(self):
            return True
        return False

class LockError(Exception):
    """There was a lock error on the object"""
    pass

class AlreadyLocked(LockError):
    """The object is already locked"""
    pass

class NotLocked(LockError):
    """The object is not locked"""
    pass

class Page(models.Model):
    """
    The page class to build a Wiki
    Each page may have a parent and it's URL is of the form my.site/page/<grd_pa>/<parent>/<mypage>
    It has an ID field, but don't use it, since it's only there for DB part, and because compound primary key is
    awkward!
    Prefere querying pages with Page.get_page_by_full_name()

    Be careful with the _full_name attribute: this field may not be valid until you call save(). It's made for fast
    query, but don't rely on it when playing with a Page object, use get_full_name() instead!
    """
    name = models.CharField(_('page name'), max_length=30, blank=False)
    parent = models.ForeignKey('self', related_name="children", null=True, blank=True, on_delete=models.SET_NULL)
    # Attention: this field may not be valid until you call save(). It's made for fast query, but don't rely on it when
    # playing with a Page object, use get_full_name() instead!
    _full_name = models.CharField(_('page name'), max_length=255, blank=True)
    owner_group = models.ForeignKey(Group, related_name="owned_page",
                                    default=settings.SITH_GROUPS['root']['id'])
    edit_groups = models.ManyToManyField(Group, related_name="editable_page", blank=True)
    view_groups = models.ManyToManyField(Group, related_name="viewable_page", blank=True)
    lock_mutex = {}


    class Meta:
        unique_together = ('name', 'parent')
        permissions = (
            ("change_prop_page", "Can change the page's properties (groups, ...)"),
            ("view_page", "Can view the page"),
        )

    @staticmethod
    def get_page_by_full_name(name):
        """
        Quicker to get a page with that method rather than building the request every time
        """
        return Page.objects.filter(_full_name=name).first()

    def __init__(self, *args, **kwargs):
        super(Page, self).__init__(*args, **kwargs)

    def clean(self):
        """
        Cleans up only the name for the moment, but this can be used to make any treatment before saving the object
        """
        if '/' in self.name:
            self.name = self.name.split('/')[-1]
        if Page.objects.exclude(pk=self.pk).filter(_full_name=self.get_full_name()).exists():
            raise ValidationError(
                _('Duplicate page'),
                code='duplicate',
            )
        super(Page, self).clean()
        if self.parent is not None and self in self.get_parent_list():
            raise ValidationError(
                _('Loop in page tree'),
                code='loop',
            )

    def get_parent_list(self):
        l = []
        p = self.parent
        while p is not None:
            l.append(p)
            p = p.parent
        return l

    def save(self, *args, **kwargs):
        """
        Performs some needed actions before and after saving a page in database
        """
        if not self.is_locked():
            raise NotLocked("The page is not locked and thus can not be saved")
        self.full_clean()
        # This reset the _full_name just before saving to maintain a coherent field quicker for queries than the
        # recursive method
        # It also update all the children to maintain correct names
        self._full_name = self.get_full_name()
        for c in self.children.all():
            c.save()
        super(Page, self).save(*args, **kwargs)
        self.unset_lock()

    def is_locked(self):
        """
        Is True if the page is locked, False otherwise
        This is where the timeout is handled, so a locked page for which the timeout is reach will be unlocked and this
        function will return False
        """
        if self.pk not in Page.lock_mutex.keys():
            # print("Page mutex does not exists")
            return False
        if (timezone.now()-Page.lock_mutex[self.pk]['time']) > timedelta(minutes=5):
            # print("Lock timed out")
            self.unset_lock()
            return False
        return True

    def set_lock(self, user):
        """
        Sets a lock on the current page or raise an AlreadyLocked exception
        """
        if self.is_locked() and self.get_lock()['user'] != user:
            raise AlreadyLocked("The page is already locked by someone else")
        Page.lock_mutex[self.pk] = {'user': user,
                                    'time': timezone.now()}
        # print("Locking page")

    def set_lock_recursive(self, user):
        """
        Locks recursively all the child pages for editing properties
        """
        for p in self.children.all():
            p.set_lock_recursive(user)
        self.set_lock(user)

    def unset_lock(self):
        """Always try to unlock, even if there is no lock"""
        Page.lock_mutex.pop(self.pk, None)
        # print("Unlocking page")

    def get_lock(self):
        """
        Returns the page's mutex containing the time and the user in a dict
        """
        if self.is_locked():
            return Page.lock_mutex[self.pk]
        raise NotLocked("The page is not locked and thus can not return its mutex")

    def get_absolute_url(self):
        """
        This is needed for black magic powered UpdateView's children
        """
        return reverse('core:page', kwargs={'page_name': self._full_name})

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        """
        Computes the real full_name of the page based on its name and its parent's name
        You can and must rely on this function when working on a page object that is not freshly fetched from the DB
        (For example when treating a Page object coming from a form)
        """
        if self.parent is None:
            return self.name
        return '/'.join([self.parent.get_full_name(), self.name])

    def get_display_name(self):
        return self.get_full_name()

class PageRev(models.Model):
    """
    This is the true content of the page.
    Each page object has a revisions field that is a list of PageRev, ordered by date.
    my_page.revisions.last() gives the PageRev object that is the most up-to-date, and thus,
    is the real content of the page.
    The content is in PageRev.title and PageRev.content .
    """
    title = models.CharField(_("page title"), max_length=255, blank=True)
    content = models.TextField(_("page content"), blank=True)
    date = models.DateTimeField(_('date'), auto_now=True)
    author = models.ForeignKey(User, related_name='page_rev')
    page = models.ForeignKey(Page, related_name='revisions')

    class Meta:
        ordering = ['date',]

    def get_absolute_url(self):
        """
        This is needed for black magic powered UpdateView's children
        """
        return reverse('core:page', kwargs={'page_name': self.page._full_name})

    def __str__(self):
        return str(self.__dict__)

    def __getattribute__(self, attr):
        if attr == "owner_group":
            return self.page.owner_group
        elif attr == "edit_groups":
            return self.page.edit_groups
        elif attr == "view_groups":
            return self.page.view_groups
        elif attr == "unset_lock":
            return self.page.unset_lock
        else:
            return object.__getattribute__(self, attr)

    def save(self, *args, **kwargs):
        super(PageRev, self).save(*args, **kwargs)
        # Don't forget to unlock, otherwise, people will have to wait for the page's timeout
        self.page.unset_lock()

