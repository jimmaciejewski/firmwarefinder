from django.core.management.base import BaseCommand
from firmware.models import Version


class Command(BaseCommand):
    help = 'Ensures all versions have a created date'

    def handle(self, *args, **options):
        for version in Version.objects.all():
           sub, created = Subscriber.objects.get_or_create(user=user)
           if created:
               self.stdout.write(self.style.SUCCESS(f'Created subscriber for {user}'))
           else:
               self.stdout.write(self.style.WARNING(f"Found existing {sub} for {user}"))