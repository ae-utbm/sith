from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.management import call_command

from core.models import User, RealGroup
from com.models import Sith

class ComTest(TestCase):
    def setUp(self):
        call_command("populate")
        self.skia = User.objects.filter(username="skia").first()
        self.com_group = RealGroup.objects.filter(id=settings.SITH_GROUP_COM_ADMIN_ID).first()
        self.skia.groups = [self.com_group]
        self.skia.save()
        self.client.login(username=self.skia.username, password='plop')

    def test_alert_msg(self):
        response = self.client.post(reverse("com:alert_edit"), {"alert_msg": """
### ALERTE!

**Caaaataaaapuuuulte!!!!**
"""})
        r = self.client.get(reverse("core:index"))
        self.assertTrue(r.status_code == 200)
        self.assertTrue("""<div id="alert_box">\\n            <h3>ALERTE!</h3>\\n<p><strong>Caaaataaaapuuuulte!!!!</strong></p>""" in str(r.content))

    def test_info_msg(self):
        response = self.client.post(reverse("com:info_edit"), {"info_msg": """
### INFO: **Caaaataaaapuuuulte!!!!**
"""})
        r = self.client.get(reverse("core:index"))
        self.assertTrue(r.status_code == 200)
        self.assertTrue("""<div id="info_box">\\n            <h3>INFO: <strong>Caaaataaaapuuuulte!!!!</strong></h3>""" in str(r.content))

