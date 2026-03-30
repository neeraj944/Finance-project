from django.apps import AppConfig


class ForecastAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'forecast_app'


    def ready(self):
        import forecast_app.signals
