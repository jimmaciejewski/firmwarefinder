from django.core.management.base import BaseCommand, CommandError
from firmware.models import Site, Product, Firmware, Version
from django.utils import timezone

import requests
from bs4 import BeautifulSoup
from pprint import pprint
import json

class Command(BaseCommand):
    help = 'Scrapes all sites for firmware'

    def handle(self, *args, **options):
        self.by_site()

    def by_version(self):
        data = {}
        data['name'] = "Version"
        data['children'] = []
        for i, version in enumerate(Version.objects.all()):
            data['children'].append({'name': version.number, 'children': []})
            data['children']


    def by_product(self):
        data = {}
        product = Product.objects.get(name="DGX1600-ENC")
        data['name'] = product.name
        data['children'] = []
        for i, firmware in enumerate(Firmware.objects.filter(products=product)):
            data['children'].append({'name': firmware.name, 'children': []})
            for version in firmware.version_set.all():
                data['children'][i]['children'].append({'name': version.number, 'value': version.file_size})

        with open('by_product.json', 'w') as f:
            f.write(json.dumps(data))


    def by_site(self):
        data = {}
        site = Site.objects.get(name="AMX")
        data['name'] = site.name
        data['children'] = []
        for i, product in enumerate(Product.objects.filter(site=site)):
            data['children'].append({'name': product.name, 'children': []})
            for j, firmware in enumerate(product.firmware_set.all()):
                data['children'][i]['children'].append({'name': firmware.name, 'children': []})
                for version in firmware.version_set.all():
                    data['children'][i]['children'][j]['children'].append({'name': version.number, 'value': 100})

        with open('by_site.json', 'w') as f:
            f.write(json.dumps(data))