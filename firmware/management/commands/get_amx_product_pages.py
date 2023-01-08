from django.core.management.base import BaseCommand, CommandError
from firmware.models import Product, Brand, Version, FG, AssociatedName
from django.utils import timezone
from django.db.utils import IntegrityError
from dataclasses import dataclass, field
import requests
import re
from bs4 import BeautifulSoup

@dataclass
class FirmwareVersion:
    name: str = None
    version_number: str = None
    download_page: str = None
    language: str = None
    file_size: str = None
    product_page_date: str = None

@dataclass
class Captured:
    
    versions: list = field(default_factory=list)
    fgs: list = field(default_factory=list)

class Command(BaseCommand):
    help = 'Gets AMX product pages and extracts FGs'

    def handle(self, *args, **options):
        brand = Brand.objects.get(name='AMX')
        for product in Product.objects.filter(brand=brand):
            headers = {'user-agent': 'FirmwareTracker'}
            corrected_name = product.name.replace('/', '-').replace(' ', '-')
            url = f"{brand.base_url}/en-US/products/{corrected_name}"
            response = requests.get(url, headers=headers)
            
            self.parse_page(response.text, brand, product)

    def parse_page(self, html: str, brand: Brand, product: Product):
        self.stdout.write(self.style.SUCCESS(f'Parsing {product.name} for firmware'))
        cap = Captured()
        soup = BeautifulSoup(html, 'html.parser')
        try:
            rows = soup.body.table("tr")
        except TypeError:
            # This probably means the page doesn't exist or something is different
            self.stdout.write(self.style.WARNING(f"Unable to parse, brand: {brand.name}, product: {product.name}"))
            return
        at_firmware = False
        for row in rows:
            if at_firmware and row("h6"):
                # This means we have finished the firmware section
                break
            if at_firmware:
                version = FirmwareVersion()
                # This should be a firmware
                # td 0 is the firmware link and name
                version.name = row("td")[0]("a")[0].text.strip()
            
                # new_firmware, _ = Version.objects.get_or_create(name=name)
                # new_firmware.products.add(product)

                # td 1 is the version
                version.version_number = row("td")[1].text.strip()

                # new_version, created = Version.objects.get_or_create(firmware=new_firmware, number=version)
                # if created:
                #     self.stdout.write(self.style.NOTICE(f"Found a new version of firmware for {product}: Firmware {new_firmware.name} Version {version}"))
                
                # new_version.download_page = row("td")[0]("a")[0].get('href')
                version.download_page = row("td")[0]("a")[0].get('href')

                
                # td 2 is the language (can be blank)
                # new_version.language = row("td")[2].text.strip()
                version.language = row("td")[2].text.strip()
                # td 3 is the file size
                # new_version.file_size = row("td")[3].text.strip()
                version.file_size = row("td")[3].text.strip()
                # td 4 is the date
                # new_version.product_page_date = row("td")[4].text.strip()
                version.product_page_date = row("td")[4].text.strip()
                # new_version.date_last_seen = timezone.now()
                # new_version.save()
                # new_firmware.save()
                cap.versions.append(version)

            if "Firmware" in str(row):
                at_firmware = True
        # Try to get the specs table
        try:
            rows = soup.body("table", {"class":"specs"})[0]("tr")
        except (TypeError, IndexError):
            # This probably means the page doesn't exist or something is different
            self.stdout.write(self.style.WARNING(f"Unable find specs for, brand: {brand.name}, product: {product.name}"))
            return
        for row in rows:
            if "FG Numbers" in row.text:
                # single_fg = row.text.replace("FG Numbers", "").strip()
                # Make sure it is valid
                # if len(single_fg) > 20:
                # with open('fgs.txt', 'a') as f:
                    # f.write(row.text + "\n")
                # try using re?
                regex = r"(?P<FG>FGN?\d{4}-?\d{0,4}-?[A-Z]{0,2}-?[A-Z]{0,2}-?\d{0,2})\n?\ ?"
                matches = re.finditer(regex, row.text, re.MULTILINE)
                for match in matches:
                    cap.fgs.append(match.group().replace(',', '').strip())
                if cap.fgs == []:
                    regex = r"(?P<FG>AMX-\D{2}-\D{2}-\d{3})"
                    matches = re.finditer(regex, row.text, re.MULTILINE)
                    for match in matches:
                        cap.fgs.append(match.group().replace(',', '').strip())

                # self.stdout.write(self.style.WARNING(f"Removing an invalid(too long) fg: {cap.fg}"))
                # cap.fg = None
        # Use new cap to product objects
        try:
            

            for version in cap.versions:
                new_version, _ = Version.objects.get_or_create(number=version.version_number,
                                                               name=version.name,
                                                               download_page=version.download_page,
                                                               download_url=f"https://www.amx.com{version.download_page}/download")

                for fg in cap.fgs:
                    new_fg, _ = FG.objects.get_or_create(number=fg)
                    new_version.fgs.add(new_fg)
                    product.fgs.add(new_fg)                             
                new_version.date_last_seen = timezone.now()

                new_version.save()


                new_a_name, _ = AssociatedName.objects.get_or_create(name=version.name)
                product.associated_names.add(new_a_name)
            
            product.save()
        except IntegrityError:
            print(f"got an error on {product}")
            