from django.core.management.base import BaseCommand
from firmware.models import Version
import requests

class Command(BaseCommand):
    help = 'Verify the link is good on every version'

    def handle(self, *args, **options):
        for version in Version.objects.filter():
            if version.local_file:
                r = requests.head(url=version.local_file.url)
                if r.status_code != 200:
                    self.stdout.write(self.style.ERROR(f"{version} has a bad link, code: {r.status_code}"))
                else:
                    self.stdout.write(self.style.SUCCESS(f"{version} has a good link!"))
