from django.apps import AppConfig


class CashandbankConfig(AppConfig):
    name = 'apps.cashandbank'
    
    def ready(self):
        """Register signals when app is ready"""
        import apps.cashandbank.signals  # noqa: F401
