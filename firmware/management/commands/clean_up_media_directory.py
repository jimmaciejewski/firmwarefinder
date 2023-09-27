from django.core.management.base import BaseCommand
from django.conf import settings
from firmware.models import Version
import os


class Command(BaseCommand):
    help = 'Removes any unused or oversized files in the media directory'

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--dry_run',
            action='store_true',
            help='Dont actually remove anything',
        )

    def handle(self, *args, **options):
        '''Get a list of the files in the media directory check if they are too big or not being used'''
        self.stdout.write(self.style.SUCCESS('Checking files in media directory....'))
        if options['dry_run']:
            self.stdout.write(self.style.SUCCESS('In DRY RUN mode....'))
        for path, subdirs, files in os.walk(settings.MEDIA_ROOT):
            for name in files:
                # First check if we are using the file
                folder = os.path.split(path)[1]
                local_file_name = os.path.join(folder, name)
                try:
                    version = Version.objects.get(local_file=local_file_name)
                except Exception as error:
                    self.stdout.write(self.style.WARNING(f'{error}'))
                    self.stdout.write(self.style.WARNING(f'Unable to find version, removing: {local_file_name}'))
                    if not options['dry_run']:
                        os.remove(os.path.join(path, name))
                    continue
                # Check if the file is too big
                if os.path.getsize(os.path.join(path, name)) >= settings.FIRMWARE_VERSION_MAX_SIZE:
                    self.stdout.write(self.style.WARNING(f'Need to remove oversized file {local_file_name}'))
                    if not options['dry_run']:
                        self.stdout.write(self.style.WARNING(f'Removing local_file link {local_file_name}'))
                        version.local_file.delete()
                        version.save()
            if not files and os.path.split(path)[1] != 'media':
                self.stdout.write(self.style.WARNING(f"Removing extra folder: {path}"))
                if not options['dry_run']:
                    os.rmdir(path)

        self.stdout.write(self.style.SUCCESS('Checking all version linked files are valid'))
        for version in Version.objects.all():
            if version.local_file:
                if not os.path.exists(version.local_file.path):
                    self.stdout.write(self.style.WARNING(f'I should remove local file as I cannot find it: {version.local_file}'))
                    if not options['dry_run']:
                        version.local_file.delete()
                        version.save()
                else:
                    self.stdout.write(self.style.SUCCESS(f'This file is fine: {version.local_file}'))

