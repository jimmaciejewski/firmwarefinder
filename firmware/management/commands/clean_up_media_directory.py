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
        if options['dry_run']:
            print('In DRY RUN mode....')
        for path, subdirs, files in os.walk(settings.MEDIA_ROOT):
            for name in files:
                # First check if we are using the file
                folder = os.path.split(path)[1]
                local_file_name = f"{folder}/{name}"
                try:
                    version = Version.objects.get(local_file=f"{local_file_name}")
                except Exception as error:
                    print(error)
                    print(f'remove {local_file_name}')
                    if not options['dry_run']:
                        os.remove(os.path.join(path, name))
                    continue
                # Check if the file is too big
                if os.path.getsize(os.path.join(path, name)) >= settings.FIRMWARE_VERSION_MAX_SIZE:
                    print(f'need to remove oversized file {local_file_name}')
                    if not options['dry_run']:
                        version.local_file.delete()
                        version.save()
            if not files and os.path.split(path)[1] != 'media':
                print(f"remove folder {path}")
                if not options['dry_run']:
                    os.rmdir(path)
