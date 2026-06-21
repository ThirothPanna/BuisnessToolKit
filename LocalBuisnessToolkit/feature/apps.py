from django.apps import AppConfig

class FeatureConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'feature'
    
    def ready(self):
        # Import signals to register model event handlers (notifications)
        try:
            import feature.signals  # noqa: F401
        except Exception:
            pass