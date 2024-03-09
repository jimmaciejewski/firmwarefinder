from django.db import models
from zipfile import ZipFile, BadZipFile
from django.core.files import File
from django.contrib.auth.models import User
from django.conf import settings
import os

import requests
from tempfile import TemporaryFile



class Brand(models.Model):
    """ The Brand of the product ie AMX BSS Crown
        base_url ie www.amx.com
        extra_path maybe used by the template ie /en-US/products/
    """
    name = models.CharField(max_length=200)
    base_url = models.CharField(max_length=200, unique=True)
    extra_path = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.base_url


class FG(models.Model):
    """ An FG number
        It is related to a specific product (and variations of that product color/ amp size)
        It is also related to all useable firmware versions
    """
    number = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return f"{self.number}"


class AssociatedName(models.Model):
    """ The associated names, these are the names that products are referred to.
        For example:
        NMX-ENC-N2412A Encoder
        or N2412A
        or ENC-N2412A
        or n2400-svsi-hotfix-firmware-updater
    """
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return f"{self.name}"


class Product(models.Model):
    """ This is the official name of the product
        For example: NMX-ENC-2412A
        We will only use this name on our site
    """
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    fgs = models.ManyToManyField(FG)
    associated_names = models.ManyToManyField(AssociatedName, blank=True)
    discontinued = models.BooleanField(default=False)
    store_firmware_versions_locally = models.BooleanField(default=True)

    name = models.CharField(max_length=200, unique=True)

    def create_dashless_associated_name(self):
        """Used for search for example DX-TX will create an associated name DXTX"""
        dashless_name = self.name.replace('-', '')
        new_associated_name, _ = AssociatedName.objects.get_or_create(name=dashless_name)
        return new_associated_name

    def save(self, *args, **kwargs):
        product = super().save(*args, **kwargs)
        new_name = self.create_dashless_associated_name()
        self.associated_names.add(new_name)
        return product

    def __str__(self):
        return f"{self.name}"


def upload_path_name(name):
    replacement_list = ['/', ' ', ':', '&', '(', ')']
    for item in replacement_list:
        name = name.replace(item, '-')
    # Remove trailing -
    if name[-1] == '-':
        name = name[:-1]
    # Remove double --
    name.replace('--', '-')
    # Just in case :)
    name.replace('--', '-')
    return name


def upload_location(instance, filename):
    my_path = upload_path_name(instance.name)
    return os.path.join(my_path, filename)


class Version(models.Model):
    """ This is a specific firmware version
    """
    fgs = models.ManyToManyField(FG, blank=True)
    name = models.CharField(max_length=200)
    number = models.CharField(max_length=200)
    download_page = models.CharField(max_length=200, blank=True)
    download_url = models.CharField(max_length=200, blank=True)
    local_file = models.FileField(upload_to=upload_location, max_length=200, null=True, blank=True)
    date_last_seen = models.DateTimeField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    read_me = models.TextField(blank=True)
    read_me_path = models.CharField(max_length=200, blank=True, default="Readme.txt")

    do_not_download = models.BooleanField(default=False)

    hotfix = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.local_file and self.read_me == "":
            self.read_me = self.get_release_notes()
        if self.read_me != "Readme.txt not found...":
            self.get_fgs()
        super().save(*args, **kwargs)

    def get_release_notes(self):
        read_me = "Unable to find readme"
        if not self.read_me_path:
            return "No readme in this firmware"
        possible_encodings = ['utf-8', 'Windows-1252']

        try:
            fh = self.local_file.path
            with ZipFile(fh) as myzip:
                # For SVSi firmware
                for item in myzip.filelist:
                    if 'readme' in item.filename.lower():
                        location = item.filename
                        break
                else:
                    location = self.read_me_path
                with myzip.open(location) as myfile:
                    raw_file = myfile.read()
                    for my_encoding in possible_encodings:
                        try:
                            return raw_file.decode(encoding=my_encoding)
                        except UnicodeDecodeError:
                            pass
                    print(f"Unable to read readme.txt encoding?: {self.name}")
        except KeyError:
            # print(f"Did not find: {self.name}: {self.read_me_path}")
            pass
        except BadZipFile as error:
            print(f"Not a zip file? {self.name}: {error}")
            # If it isn't a zip file just return
            return read_me
        except NotImplementedError as error:
            print(f"Zip error {self.name}: {error}")
            # If we are not able to read the zip file just return
            return read_me
        print(f"Unable to find readme {self.name}")
        return read_me

    def get_fgs(self):
        for fg in FG.objects.all():
            if fg.number in self.read_me:
                self.fgs.add(fg)

    def download_firmware(self):
        # Lets check if we have a local copy first

        with TemporaryFile() as tf:

            # Just get head first
            headers = {'user-agent': 'FirmwareTracker'}
            r = requests.head(self.download_url, headers=headers, allow_redirects=True)

            # Check file length no local copy if it is too big
            if 'content-length' in r.headers:
                if int(r.headers['content-length']) >= settings.FIRMWARE_VERSION_MAX_SIZE:
                    print(f'The version file is too large: {self.name}')
                    return

            filename = os.path.basename(r.url).replace('%20', '_').replace('%2B', '+')
            r = requests.get(self.download_url, headers=headers, stream=True)

            for chunk in r.iter_content(chunk_size=4096):
                tf.write(chunk)
            tf.seek(0)
            self.local_file.save(f"{filename}", File(tf))

    def __str__(self):
        return f"{self.name} v{self.number}"


class Subscriber(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    send_email = models.BooleanField(default=True)
    send_email_even_if_none_found = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user}"
