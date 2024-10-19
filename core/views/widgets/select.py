from django.contrib.staticfiles.storage import staticfiles_storage
from django.forms import Select, SelectMultiple


class AutoCompleteSelectMixin:
    component_name = "autocomplete-select"
    template_name = "core/widgets/autocomplete_select.jinja"
    is_ajax = False

    def optgroups(self, name, value, attrs=None):
        """Don't create option groups when doing ajax"""
        if self.is_ajax:
            return []
        return super().optgroups(name, value, attrs=attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["component"] = self.component_name
        context["statics"] = {
            "js": staticfiles_storage.url(
                "webpack/core/components/ajax-select-index.ts"
            ),
            "csss": [
                staticfiles_storage.url(
                    "webpack/core/components/ajax-select-index.css"
                ),
                staticfiles_storage.url("core/components/ajax-select.scss"),
            ],
        }
        return context


class AutoCompleteSelect(AutoCompleteSelectMixin, Select): ...


class AutoCompleteSelectMultiple(AutoCompleteSelectMixin, SelectMultiple): ...


class AutoCompleteSelectUser(AutoCompleteSelectMixin, Select):
    component_name = "user-ajax-select"
    is_ajax = True


class AutoCompleteSelectMultipleUser(AutoCompleteSelectMixin, SelectMultiple):
    component_name = "user-ajax-select"
    is_ajax = True
