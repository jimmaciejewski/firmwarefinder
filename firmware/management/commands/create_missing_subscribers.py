from django.core.management.base import BaseCommand
from firmware.models import Subscriber
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Downloads firmware for each version'

    def handle(self, *args, **options):
        for user in User.objects.all():
           sub, created = Subscriber.objects.get_or_create(user=user)
           if created:
               self.stdout.write(self.style.SUCCESS(f'Created subscriber for {user}'))
           else:
               self.stdout.write(self.style.WARNING(f"Found existing {sub} for {user}"))