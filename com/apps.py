from django.apps import AppConfig


class ComConfig(AppConfig):
    name = "com"
    verbose_name = "News and communication"

    def ready(self):
        import com.signals  # noqa F401
