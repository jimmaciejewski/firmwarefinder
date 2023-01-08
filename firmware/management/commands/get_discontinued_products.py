from django.core.management.base import BaseCommand, CommandError
from firmware.models import Brand, Product, FG, Version, AssociatedName

import requests
from bs4 import BeautifulSoup



class Command(BaseCommand):
    help = 'Scrapes all products from AMX discontinued product page'

    def handle(self, *args, **options):
        site = Brand.objects.get(name="AMX")
        headers = {'user-agent': 'FirmwareTracker', 'accept': 'text/html'}
        response = requests.get(f"{site.base_url}/en-US/discontinued_products", headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')

        for tr in table.findAll("tr"):
            trs = tr.findAll("td")
            model = ""
            fgs = []
            for i, item in enumerate(trs):
                if item.text == 'Model':
                    # Skip the column headers
                    break
                # 0 link and Model Name
                if i == 0:
                    model = item.text.strip()
                # 1 FG Number
                if i == 1:
                    for fg in item.text.split(','):
                        if fg == '':
                            continue
                        fgs.append(fg)
                # 2 Description
            

            new_product, created = Product.objects.get_or_create(name=model, brand=site)
            new_product.discontinued = True
            for fg in fgs:
                new_fg, _ = FG.objects.get_or_create(number=fg)
                new_product.fgs.add(new_fg)
            new_product.save()
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created: {new_product.name}'))
            else:
                self.stdout.write(self.style.NOTICE(f'Already Exists: {new_product.name}'))
