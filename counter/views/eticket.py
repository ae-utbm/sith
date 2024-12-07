#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the source code of the website at https://github.com/ae-utbm/sith
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
#

from django.http import Http404, HttpResponse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView

from core.views import CanViewMixin
from counter.forms import EticketForm
from counter.models import Eticket, Selling
from counter.views.mixins import CounterAdminMixin, CounterAdminTabsMixin


class EticketListView(CounterAdminTabsMixin, CounterAdminMixin, ListView):
    """A list view for the admins."""

    model = Eticket
    template_name = "counter/eticket_list.jinja"
    ordering = ["id"]
    current_tab = "etickets"


class EticketCreateView(CounterAdminTabsMixin, CounterAdminMixin, CreateView):
    """Create an eticket."""

    model = Eticket
    template_name = "core/create.jinja"
    form_class = EticketForm
    current_tab = "etickets"


class EticketEditView(CounterAdminTabsMixin, CounterAdminMixin, UpdateView):
    """Edit an eticket."""

    model = Eticket
    template_name = "core/edit.jinja"
    form_class = EticketForm
    pk_url_kwarg = "eticket_id"
    current_tab = "etickets"


class EticketPDFView(CanViewMixin, DetailView):
    """Display the PDF of an eticket."""

    model = Selling
    pk_url_kwarg = "selling_id"

    def get(self, request, *args, **kwargs):
        from reportlab.graphics import renderPDF
        from reportlab.graphics.barcode.qr import QrCodeWidget
        from reportlab.graphics.shapes import Drawing
        from reportlab.lib.units import cm
        from reportlab.lib.utils import ImageReader
        from reportlab.pdfgen import canvas

        if not (
            hasattr(self.object, "product") and hasattr(self.object.product, "eticket")
        ):
            raise Http404

        eticket = self.object.product.eticket
        user = self.object.customer.user
        code = "%s %s %s %s" % (
            self.object.customer.user.id,
            self.object.product.id,
            self.object.id,
            self.object.quantity,
        )
        code += " " + eticket.get_hash(code)[:8].upper()
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'filename="eticket.pdf"'
        p = canvas.Canvas(response)
        p.setTitle("Eticket")
        im = ImageReader("core/static/core/img/eticket.jpg")
        width, height = im.getSize()
        size = max(width, height)
        width = 8 * cm * width / size
        height = 8 * cm * height / size
        p.drawImage(im, 10 * cm, 25 * cm, width, height)
        if eticket.banner:
            im = ImageReader(eticket.banner)
            width, height = im.getSize()
            size = max(width, height)
            width = 6 * cm * width / size
            height = 6 * cm * height / size
            p.drawImage(im, 1 * cm, 25 * cm, width, height)
        if user.profile_pict:
            im = ImageReader(user.profile_pict.file)
            width, height = im.getSize()
            size = max(width, height)
            width = 150 * width / size
            height = 150 * height / size
            p.drawImage(im, 10.5 * cm - width / 2, 16 * cm, width, height)
        if eticket.event_title:
            p.setFont("Helvetica-Bold", 20)
            p.drawCentredString(10.5 * cm, 23.6 * cm, eticket.event_title)
        if eticket.event_date:
            p.setFont("Helvetica-Bold", 16)
            p.drawCentredString(
                10.5 * cm, 22.6 * cm, eticket.event_date.strftime("%d %b %Y")
            )  # FIXME with a locale
        p.setFont("Helvetica-Bold", 14)
        p.drawCentredString(
            10.5 * cm,
            15 * cm,
            "%s : %d %s"
            % (user.get_display_name(), self.object.quantity, str(_("people(s)"))),
        )
        p.setFont("Courier-Bold", 14)
        qrcode = QrCodeWidget(code)
        bounds = qrcode.getBounds()
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        d = Drawing(260, 260, transform=[260.0 / width, 0, 0, 260.0 / height, 0, 0])
        d.add(qrcode)
        renderPDF.draw(d, p, 10.5 * cm - 130, 6.1 * cm)
        p.drawCentredString(10.5 * cm, 6 * cm, code)

        partners = ImageReader("core/static/core/img/partners.png")
        width, height = partners.getSize()
        size = max(width, height)
        width = width * 2 / 3
        height = height * 2 / 3
        p.drawImage(partners, 0 * cm, 0 * cm, width, height)

        p.showPage()
        p.save()
        return response
