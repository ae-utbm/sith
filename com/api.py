from pathlib import Path

from django.conf import settings
from django.http import Http404
from ninja_extra import ControllerBase, api_controller, route

from com.models import IcsCalendar
from core.views.files import send_raw_file


@api_controller("/calendar")
class CalendarController(ControllerBase):
    CACHE_FOLDER: Path = settings.MEDIA_ROOT / "com" / "calendars"

    @route.get("/external.ics")
    def calendar_external(self):
        """Return the ICS file of the AE Google Calendar

        Because of Google's cors rules, we can't "just" do a request to google ics
        from the frontend. Google is blocking CORS request in it's responses headers.
        The only way to do it from the frontend is to use Google Calendar API with an API key
        This is not especially desirable as your API key is going to be provided to the frontend.

        This is why we have this backend based solution.
        """
        if (calendar := IcsCalendar.get_external()) is not None:
            return send_raw_file(calendar)
        raise Http404

    @route.get("/internal.ics")
    def calendar_internal(self):
        return send_raw_file(IcsCalendar.get_internal())
