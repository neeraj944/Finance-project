# forecast_app/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .utils import create_default_categories, create_default_payment_modes

@receiver(post_save, sender=User)
def create_user_defaults(sender, instance, created, **kwargs):
    if created:
        create_default_categories(instance)
        create_default_payment_modes(instance)
