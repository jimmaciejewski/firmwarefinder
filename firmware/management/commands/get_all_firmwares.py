from django.core.management.base import BaseCommand, CommandError
from firmware.models import Product, Brand, Version, FG, AssociatedName
from django.utils import timezone
from django.db.utils import IntegrityError

import requests




class Command(BaseCommand):
    help = 'Downloads firmware for each version'

    def handle(self, *args, **options):
        for version in Version.objects.all():
            if not version.local_file:
                self.stdout.write(self.style.SUCCESS(f'Downloading a firmware version: {version.name}'))
                version.download_firmware()
            else:
                self.stdout.write(self.style.WARNING(f'Skipping Already Downloaded: {version.name}'))