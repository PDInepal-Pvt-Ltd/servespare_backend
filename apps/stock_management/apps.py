from django.apps import AppConfig


class StockManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.stock_management'
    def ready(self):
        """Register signals when app is ready"""
        import apps.stock_management.signals  # noqa: F401