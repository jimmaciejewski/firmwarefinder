from django.core.management.base import BaseCommand
from firmware.models import Version


class Command(BaseCommand):
    help = 'Downloads firmware for each version'

    def handle(self, *args, **options):
        for version in Version.objects.all():
            if not version.local_file:
                self.stdout.write(self.style.SUCCESS(f'Downloading a firmware version: {version.name}'))
                version.download_firmware()
