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
import logging

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import models
from django.http import HttpResponse
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.timezone import localdate
from django.views.generic import DeleteView, ListView
from django.views.generic.edit import CreateView, FormView

from core.models import OperationLog, SithFile, User, UserBan
from core.views import CanEditPropMixin
from counter.models import Customer
from forum.models import ForumMessageMeta
from rootplace.forms import BanForm, BanReportForm, MergeForm, SelectUserForm


def __merge_subscriptions(u1: User, u2: User):
    """Give all the subscriptions of the second user to first one.

    If some subscriptions are still active, update their end date
    to increase the overall subscription time of the first user.

    Some examples :
    - if u1 is not subscribed, his subscription end date become the one of u2
    - if u1 is subscribed but not u2, nothing happen
    - if u1 is subscribed for, let's say,
      2 remaining months and u2 is subscribed for 3 remaining months,
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
            if subscription.subscription_start > localdate():
                remaining = subscription.subscription_end - localdate()
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
    """Merge u2 into u1.

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
        Customer.objects.filter(pk=c_dest.pk).update_amount()
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


def delete_all_forum_user_messages(
    user: User, moderator: User, *, verbose: bool = False
):
    """Soft delete all messages of a user.

    Args:
        user: core.models.User the user to delete messages from
        moderator: core.models.User the one marked as the moderator.
        verbose: bool if True, print the deleted messages
    """
    for message in user.forum_messages.all():
        if message.is_deleted():
            continue

        if verbose:
            logging.getLogger("django").info(message)
        ForumMessageMeta(message=message, user=moderator, action="DELETE").save()


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
    """Delete all forum messages from an user.

    Messages are soft deleted and are still visible from admins
    GUI frontend to the dedicated command.
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
    """List all logs."""

    model = OperationLog
    template_name = "rootplace/logs.jinja"
    ordering = ["-date"]
    paginate_by = 100


class BanView(PermissionRequiredMixin, ListView):
    """[UserBan][core.models.UserBan] management view.

    Displays :

    - the list of active bans with their main information,
      with a link to [BanDeleteView][rootplace.views.BanDeleteView] for each one
    - a link which redirects to [BanCreateView][rootplace.views.BanCreateView]
    """

    permission_required = "core.view_userban"
    template_name = "rootplace/userban.jinja"
    queryset = UserBan.objects.select_related("user", "user__profile_pict", "ban_group")
    ordering = "created_at"
    context_object_name = "user_bans"


class BanCreateView(PermissionRequiredMixin, CreateView):
    """[UserBan][core.models.UserBan] creation view."""

    permission_required = "core.add_userban"
    form_class = BanForm
    template_name = "core/create.jinja"
    success_url = reverse_lazy("rootplace:ban_list")


class BanDeleteView(PermissionRequiredMixin, DeleteView):
    """[UserBan][core.models.UserBan] deletion view."""

    permission_required = "core.delete_userban"
    pk_url_kwarg = "ban_id"
    model = UserBan
    template_name = "core/delete_confirm.jinja"
    success_url = reverse_lazy("rootplace:ban_list")


class BanReportPDFView(PermissionRequiredMixin, FormView):
    """Generate a PDF report of banned users at a specific date.

    Shows banned users for a selected date with two display modes:
    - image: Only profile pictures in a grid
    - desc: Detailed list with name, first name, reason, and profile picture
    """

    permission_required = "core.view_userban"
    template_name = "rootplace/ban_report.jinja"
    form_class = BanReportForm

    def form_valid(self, form):
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.pdfgen import canvas

        selected_date = form.cleaned_data["date"]
        mode = form.cleaned_data["mode"]
        ban_group = form.cleaned_data.get("ban_group")

        # Get bans active on the selected date
        banned_users = UserBan.objects.filter(
            created_at__date__lte=selected_date
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__date__gte=selected_date)
        )

        # Apply optional ban_group filter
        if ban_group:
            banned_users = banned_users.filter(ban_group=ban_group)

        banned_users = banned_users.select_related("user", "user__profile_pict", "ban_group")

        # Create PDF response
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="banned_users_{selected_date}.pdf"'
        )

        # Create PDF canvas
        p = canvas.Canvas(response, pagesize=A4)
        width, height = A4
        p.setTitle(f"Utilisateurs bannis - {selected_date}")

        # Title
        p.setFont("Helvetica-Bold", 20)
        p.drawCentredString(width / 2, height - 2 * cm, "Utilisateurs bannis")
        p.setFont("Helvetica", 14)
        title_text = selected_date.strftime("%d/%m/%Y")
        if ban_group:
            title_text += f" - {ban_group.name}"
        p.drawCentredString(width / 2, height - 2.8 * cm, title_text)

        if mode == "image":
            # Image mode: Grid of profile pictures
            self._generate_image_mode(p, banned_users, width, height, selected_date, ban_group)
        else:
            # Desc mode: Detailed list with name, reason and image
            self._generate_desc_mode(p, banned_users, width, height, selected_date, ban_group)

        p.showPage()
        p.save()
        return response

    def _generate_image_mode(self, p, banned_users, width, height, selected_date, ban_group=None):
        """Generate PDF in image mode: grid of profile pictures."""
        from reportlab.lib.units import cm
        from reportlab.lib.utils import ImageReader

        img_size = 3 * cm
        margin = 1 * cm
        spacing = 0.5 * cm
        images_per_row = 5
        start_y = height - 5 * cm  # Increased from 4cm to 5cm to avoid overlapping with title and date

        x_pos = margin
        y_pos = start_y

        for count, ban in enumerate(banned_users, start=1):
            user = ban.user

            # Draw profile picture or placeholder
            if user.profile_pict:
                try:
                    im = ImageReader(user.profile_pict.file)
                    p.drawImage(im, x_pos, y_pos - img_size, img_size, img_size, preserveAspectRatio=True, mask='auto')
                except Exception:
                    self._draw_placeholder(p, x_pos, y_pos - img_size, img_size)
            else:
                self._draw_placeholder(p, x_pos, y_pos - img_size, img_size)

            if count % images_per_row == 0:
                # New row
                x_pos = margin
                y_pos -= (img_size + spacing)

                # Check if we need a new page
                if y_pos - img_size < 2 * cm:
                    p.showPage()
                    # Redraw title on new page
                    p.setFont("Helvetica-Bold", 20)
                    p.drawCentredString(width / 2, height - 2 * cm, "Utilisateurs bannis")
                    p.setFont("Helvetica", 14)
                    title_text = selected_date.strftime("%d/%m/%Y")
                    if ban_group:
                        title_text += f" - {ban_group.name}"
                    p.drawCentredString(width / 2, height - 2.8 * cm, title_text)
                    y_pos = height - 5 * cm
                    x_pos = margin
            else:
                x_pos += (img_size + spacing)

    def _generate_desc_mode(self, p, banned_users, width, height, selected_date, ban_group=None):
        """Generate PDF in desc mode: detailed list with name, reason and image."""
        from reportlab.lib.units import cm
        from reportlab.lib.utils import ImageReader

        img_size = 2 * cm
        margin = 1.5 * cm
        line_height = 2.5 * cm
        y_pos = height - 4 * cm

        for ban in banned_users:
            user = ban.user

            # Check if we need a new page
            if y_pos < 3 * cm:
                p.showPage()
                # Redraw title on new page
                p.setFont("Helvetica-Bold", 20)
                p.drawCentredString(width / 2, height - 2 * cm, "Utilisateurs bannis")
                p.setFont("Helvetica", 14)
                title_text = selected_date.strftime("%d/%m/%Y")
                if ban_group:
                    title_text += f" - {ban_group.name}"
                p.drawCentredString(width / 2, height - 2.8 * cm, title_text)
                y_pos = height - 4 * cm

            # Draw profile picture
            if user.profile_pict:
                try:
                    im = ImageReader(user.profile_pict.file)
                    p.drawImage(im, margin, y_pos - img_size, img_size, img_size, preserveAspectRatio=True, mask='auto')
                except Exception:
                    self._draw_placeholder(p, margin, y_pos - img_size, img_size)
            else:
                self._draw_placeholder(p, margin, y_pos - img_size, img_size)

            # Draw user information
            text_x = margin + img_size + 0.5 * cm
            p.setFont("Helvetica-Bold", 12)
            p.drawString(text_x, y_pos - 0.5 * cm, f"{user.first_name} {user.last_name}")

            p.setFont("Helvetica", 10)
            ban_type = ban.ban_group.name if ban.ban_group else "N/A"
            p.drawString(text_x, y_pos - 1 * cm, f"Type de ban : {ban_type}")

            # Draw reason (truncate if too long)
            reason_text = ban.reason[:80] + "..." if len(ban.reason) > 80 else ban.reason
            p.setFont("Helvetica-Oblique", 9)
            p.drawString(text_x, y_pos - 1.5 * cm, f"Raison: {reason_text}")

            y_pos -= line_height

    def _draw_placeholder(self, p, x, y, size):
        """Draw a placeholder rectangle when no profile picture is available."""
        p.setFillColorRGB(0.9, 0.9, 0.9)
        p.rect(x, y, size, size, fill=1)
        p.setFillColorRGB(0, 0, 0)
        p.setFont("Helvetica", 8)
        p.drawCentredString(x + size / 2, y + size / 2, "Pas de photo")

