from django.apps import AppConfig

class DoctorAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'doctor_app'

    def ready(self):
        import doctor_app.signals
