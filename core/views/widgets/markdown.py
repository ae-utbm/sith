from django.contrib.staticfiles.storage import staticfiles_storage
from django.forms import Textarea


class MarkdownInput(Textarea):
    template_name = "core/widgets/markdown_textarea.jinja"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        context["statics"] = {
            "js": staticfiles_storage.url("bundled/core/components/easymde-index.ts"),
            "css": staticfiles_storage.url("bundled/core/components/easymde-index.css"),
        }
        return context
