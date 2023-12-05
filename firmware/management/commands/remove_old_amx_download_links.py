from django.core.management.base import BaseCommand
from firmware.models import Version


class Command(BaseCommand):
    help = 'Removes old amx.com download links'

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--dry_run',
            action='store_true',
            help='Dont actually remove anything',
        )

    def handle(self, *args, **options):
        for version in Version.objects.all():
            if version.download_url.startswith('https://www.amx.com/en-US/softwares/'):
                if not options['dry_run']:
                    version.delete()
                    self.stdout.write(self.style.SUCCESS(f'Removed {version.name}'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'Would have removed {version.name}'))
