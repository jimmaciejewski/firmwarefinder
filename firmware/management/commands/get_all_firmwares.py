from django.core.management.base import BaseCommand
from firmware.models import Product, Version


class Command(BaseCommand):
    help = 'Downloads firmware for each version'

    def handle(self, *args, **options):
        for version in Version.objects.all():
            related_products = Product.objects.filter(fgs__in=version.fgs.all())
            if any([product.store_firmware_versions_locally for product in related_products]):
                self.stdout.write(self.style.WARNING(f'Not downloading a local copy of {version.name}'))
                continue
            if not version.local_file:
                self.stdout.write(self.style.SUCCESS(f'Downloading a firmware version: {version.name}'))
                version.download_firmware()
