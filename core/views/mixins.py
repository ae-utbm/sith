from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.views import View


class TabedViewMixin(View):
    """Basic functions for displaying tabs in the template."""

    def get_tabs_title(self):
        if hasattr(self, "tabs_title"):
            return self.tabs_title
        raise ImproperlyConfigured("tabs_title is required")

    def get_current_tab(self):
        if hasattr(self, "current_tab"):
            return self.current_tab
        raise ImproperlyConfigured("current_tab is required")

    def get_list_of_tabs(self):
        if hasattr(self, "list_of_tabs"):
            return self.list_of_tabs
        raise ImproperlyConfigured("list_of_tabs is required")

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["tabs_title"] = self.get_tabs_title()
        kwargs["current_tab"] = self.get_current_tab()
        kwargs["list_of_tabs"] = self.get_list_of_tabs()
        return kwargs


class QuickNotifMixin:
    quick_notif_list = []

    def dispatch(self, request, *arg, **kwargs):
        # In some cases, the class can stay instanciated, so we need to reset the list
        self.quick_notif_list = []
        return super().dispatch(request, *arg, **kwargs)

    def get_success_url(self):
        ret = super().get_success_url()
        if hasattr(self, "quick_notif_url_arg"):
            if "?" in ret:
                ret += "&" + self.quick_notif_url_arg
            else:
                ret += "?" + self.quick_notif_url_arg
        return ret

    def get_context_data(self, **kwargs):
        """Add quick notifications to context."""
        kwargs = super().get_context_data(**kwargs)
        kwargs["quick_notifs"] = []
        for n in self.quick_notif_list:
            kwargs["quick_notifs"].append(settings.SITH_QUICK_NOTIF[n])
        for key, val in settings.SITH_QUICK_NOTIF.items():
            for gk in self.request.GET:
                if key == gk:
                    kwargs["quick_notifs"].append(val)
        return kwargs


class AllowFragment:
    """Add `is_fragment` to templates. It's only True if the request is emitted by htmx"""

    def get_context_data(self, **kwargs):
        kwargs["is_fragment"] = self.request.headers.get("HX-Request", False)
        return super().get_context_data(**kwargs)
