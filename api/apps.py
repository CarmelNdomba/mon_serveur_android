from django.apps import AppConfig
import os


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        if os.getenv("RAILWAY_ENVIRONMENT"):
            from django.contrib.auth import get_user_model
            User = get_user_model()

            if not User.objects.filter(is_superuser=True).exists():
                User.objects.create_superuser(
                    username=os.getenv("DJANGO_SUPERUSER_USERNAME", "admin"),
                    email=os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@mail.com"),
                    password=os.getenv("DJANGO_SUPERUSER_PASSWORD", "Admin123456!")
                )
