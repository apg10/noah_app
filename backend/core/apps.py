from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = 'core'

    def ready(self):
        # Importa las señales para que se registren
        import core.signals  # noqa
