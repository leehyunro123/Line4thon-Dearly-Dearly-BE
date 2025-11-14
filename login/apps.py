from django.apps import AppConfig


class LoginkakaoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'login'
    
    def ready(self):
        """앱이 준비될 때 Signal 등록"""
        import login.models  # Signal이 등록되도록 import