from django.apps import AppConfig


class FraudConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.fraud'
    
    def ready(self):
        # Import and register rules when the app is ready
        import apps.fraud.registry
