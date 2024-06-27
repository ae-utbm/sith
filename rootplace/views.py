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

from ajax_select.fields import AutoCompleteSelectField
from django import forms
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic import ListView
from django.views.generic.edit import FormView

from core.models import OperationLog, SithFile, User
from core.views import CanEditPropMixin
from counter.models import Customer
from forum.models import ForumMessageMeta


def __merge_subscriptions(u1: User, u2: User):
    """
    Give all the subscriptions of the second user to first one
    If some subscriptions are still active, update their end date
    to increase the overall subscription time of the first user.

    Some examples :
    - if u1 is not subscribed, his subscription end date become the one of u2
    - if u1 is subscribed but not u2, nothing happen
    - if u1 is subscribed for, let's say, 2 remaining months and u2 is subscribed for 3 remaining months,
    he shall then be subscribed for 5 months
    """
    last_subscription = (
        u1.subscriptions.filter(
            subscription_start__lte=timezone.now(), subscription_end__gte=timezone.now()
        )
        .order_by("subscription_end")
        .last()
    )
    if last_subscription is not None:
        subscription_end = last_subscription.subscription_end
        for subscription in u2.subscriptions.filter(
            subscription_end__gte=timezone.now()
        ):
            subscription.subscription_start = subscription_end
            if subscription.subscription_start > timezone.now().date():
                remaining = subscription.subscription_end - timezone.now().date()
            else:
                remaining = (
                    subscription.subscription_end - subscription.subscription_start
                )
            subscription_end += remaining
            subscription.subscription_end = subscription_end
            subscription.save()
    u2.subscriptions.all().update(member=u1)


def __merge_pictures(u1: User, u2: User) -> None:
    SithFile.objects.filter(owner=u2).update(owner=u1)
    if u1.profile_pict is None and u2.profile_pict is not None:
        u1.profile_pict, u2.profile_pict = u2.profile_pict, None
    if u1.scrub_pict is None and u2.scrub_pict is not None:
        u1.scrub_pict, u2.scrub_pict = u2.scrub_pict, None
    if u1.avatar_pict is None and u2.avatar_pict is not None:
        u1.avatar_pict, u2.avatar_pict = u2.avatar_pict, None
    u2.save()
    u1.save()


def merge_users(u1: User, u2: User) -> User:
    """
    Merge u2 into u1
    This means that u1 shall receive everything that belonged to u2 :

        - pictures
        - refills of the sith account
        - purchases of any item bought on the eboutic or the counters
        - subscriptions
        - godfathers
        - godchildren

    If u1 had no account id, he shall receive the one of u2.
    If u1 and u2 were both in the middle of a subscription, the remaining
    durations stack
    If u1 had no profile picture, he shall receive the one of u2
    """
    for field in u1._meta.fields:
        if not field.is_relation and not u1.__dict__[field.name]:
            u1.__dict__[field.name] = u2.__dict__[field.name]
    for group in u2.groups.all():
        u1.groups.add(group.id)
    for godfather in u2.godfathers.exclude(id=u1.id):
        u1.godfathers.add(godfather)
    for godchild in u2.godchildren.exclude(id=u1.id):
        u1.godchildren.add(godchild)
    __merge_subscriptions(u1, u2)
    __merge_pictures(u1, u2)
    u2.invoices.all().update(user=u1)
    c_src = Customer.objects.filter(user=u2).first()
    if c_src is not None:
        c_dest, created = Customer.get_or_create(u1)
        c_src.refillings.update(customer=c_dest)
        c_src.buyings.update(customer=c_dest)
        c_dest.recompute_amount()
        if created:
            # swap the account numbers, so that the user keep
            # the id he is accustomed to
            tmp_id = c_src.account_id
            # delete beforehand in order not to have a unique constraint violation
            c_src.delete()
            c_dest.account_id = tmp_id
    u1.save()
    u2.delete()  # everything remaining in u2 gets deleted thanks to on_delete=CASCADE
    return u1


def delete_all_forum_user_messages(user, moderator, verbose=False):
    """
    Create a ForumMessageMeta that says a forum
        message is deleted on every forum message of an user
    user: the user to delete messages from
    moderator: the one marked as the moderator
    """
    for message in user.forum_messages.all():
        if message.is_deleted():
            continue

        if verbose:
            print(message)
        ForumMessageMeta(message=message, user=moderator, action="DELETE").save()


class MergeForm(forms.Form):
    user1 = AutoCompleteSelectField(
        "users", label=_("User that will be kept"), help_text=None, required=True
    )
    user2 = AutoCompleteSelectField(
        "users", label=_("User that will be deleted"), help_text=None, required=True
    )


class SelectUserForm(forms.Form):
    user = AutoCompleteSelectField(
        "users", label=_("User to be selected"), help_text=None, required=True
    )


class MergeUsersView(FormView):
    template_name = "rootplace/merge.jinja"
    form_class = MergeForm

    def dispatch(self, request, *arg, **kwargs):
        if request.user.is_root:
            return super().dispatch(request, *arg, **kwargs)
        raise PermissionDenied

    def form_valid(self, form):
        self.final_user = merge_users(
            form.cleaned_data["user1"], form.cleaned_data["user2"]
        )
        return super().form_valid(form)

    def get_success_url(self):
        return self.final_user.get_absolute_url()


class DeleteAllForumUserMessagesView(FormView):
    """
    Delete all forum messages from an user
    Messages are soft deleted and are still visible from admins
    GUI frontend to the dedicated command
    """

    template_name = "rootplace/delete_user_messages.jinja"
    form_class = SelectUserForm

    def dispatch(self, request, *args, **kwargs):
        res = super().dispatch(request, *args, **kwargs)
        if request.user.is_root:
            return res
        raise PermissionDenied

    def form_valid(self, form):
        self.user = form.cleaned_data["user"]
        delete_all_forum_user_messages(self.user, self.request.user)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("core:user_profile", kwargs={"user_id": self.user.id})


class OperationLogListView(ListView, CanEditPropMixin):
    """
    List all logs
    """

    model = OperationLog
    template_name = "rootplace/logs.jinja"
    ordering = ["-date"]
    paginate_by = 100
