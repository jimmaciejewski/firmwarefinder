from django.core.management.base import BaseCommand, CommandError
from firmware.models import Brand, Product, FG, Version, AssociatedName

import requests
from bs4 import BeautifulSoup



class Command(BaseCommand):
    help = 'Scrapes all products from AMX page'

    def handle(self, *args, **options):
        site = Brand.objects.get(name="AMX")
        headers = {'user-agent': 'FirmwareTracker'}
        response = requests.get(f"{site.base_url}/en-US/firmware", headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')

        for tr in table.findAll("tr"):
            # For each row we should create a ScrapedFirmware
            trs = tr.findAll("td")
            for i, item in enumerate(trs):
                if item.text == 'Firmware':
                    # Skip the column headers
                    break
                # 0 link and Firmware Name
                # 1 Version
                # 2 Related Products
                if i == 2:
                    if item.text.strip() == '':
                        # If there are no related products we will skip this one...
                        break
                    # Products are lists MD-1002 Acendo Book, MD-702 Acendo Book
                    for product in item.text.split(','):
                        
                        new_product, created = Product.objects.get_or_create(name=product.strip(), brand=site)
                        if created:
                            self.stdout.write(self.style.SUCCESS(f'Created: {new_product.name}'))
                        else:
                            self.stdout.write(self.style.NOTICE(f'Already Exists: {new_product.name}'))
