from django.core.management.base import BaseCommand
from django.conf import settings
from firmware.models import Version
from storages.backends.gcloud import GoogleCloudStorage
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
        storage = GoogleCloudStorage()

        for blob in storage.client.list_blobs(bucket_or_name='firmware_finder'):
            self.stdout.write(self.style.SUCCESS(f'{blob.name}'))

            # First check if we are using the file
            try:
                folder, file_name = os.path.split(blob.name)
            except Exception as error:
                self.stdout.write(self.style.WARNING(f'No Folder, ignoring? {blob.name}'))
                continue

            version = Version.objects.filter(local_file=blob.name).first()
            if version:
                self.stdout.write(self.style.SUCCESS(f'Matched file: {blob.name} on {version.name} {version.number}'))
            else:
                if not options['dry_run']:
                    storage.delete(blob.name)
                    self.stdout.write(self.style.SUCCESS(f'Removed!: {blob.name}'))
                    quit()
                else:
                    self.stdout.write(self.style.WARNING(f'Unable to find version, would be removing: {blob.name}'))
