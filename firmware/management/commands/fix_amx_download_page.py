from django.core.management.base import BaseCommand
from firmware.models import Version, Brand


class Command(BaseCommand):
    help = 'Downloads firmware for each version'

    def handle(self, *args, **options):
        brand = Brand.objects.get(name='AMX')
        for version in Version.objects.filter(hotfix=False):
            if version.download_page[:1] == '/':
                self.stdout.write(self.style.SUCCESS(f'Updating download page from  {version.download_page} to {brand.base_url}{version.download_page}'))
                version.download_page = f"{brand.base_url}{version.download_page}"
                version.save()
