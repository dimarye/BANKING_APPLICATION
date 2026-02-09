from django.apps import AppConfig


class RealtimeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.realtime'
    
    def ready(self):
        """Import signals when app is ready"""
        import apps.realtime.signals
