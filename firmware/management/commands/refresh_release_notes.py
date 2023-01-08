from django.core.management.base import BaseCommand, CommandError
from firmware.models import Version

class Command(BaseCommand):
    help = 'Gets readmes from each  firmware n'

    def handle(self, *args, **options):
        for version in Version.objects.all():
            if version.local_file:
                version.read_me = version.get_release_notes()
                version.save()
                self.stdout.write(self.style.SUCCESS(f'Updated readme on: {version.name}'))