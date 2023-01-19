from django.core.management.base import BaseCommand, CommandError
from firmware.models import Brand, Product, FG, Version, AssociatedName, SubscribedUser
from django.utils import timezone
from django.db.utils import IntegrityError

import requests
from dataclasses import dataclass, field
import json
import re
from bs4 import BeautifulSoup
from mailqueue.models import MailerMessage

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
    help = 'Checks for updates'

    def handle(self, *args, **options):
        new_found_firmwares = []
        url = "https://help.harmanpro.com/_api/web/lists/getbytitle('Pages')/Items?$top=1000&$orderby=Title&$select=PublishingPageContent,PageURL,Title,FileRef,Brand/Title, Brand/ID, Model/Title, Family/Title, DocType/Title,CaseType0/Title,FaultCategory/Title&$expand=Family,Model,CaseType0,Brand,FaultCategory,DocType&$filter=DocType/Title eq 'Hotfix firmware'"
        
        headers = {'user-agent': 'FirmwareTracker', "accept": "application/json"}
        response = requests.get(url, headers=headers)
        my_json = json.loads(response.text)

        for hotfix_page in my_json['value']:

            if hotfix_page['Brand'][0]['Title'] != 'AMX':
                continue
            new_name, _ = AssociatedName.objects.get_or_create(name=hotfix_page['Title'])
            # Get download page
            page_resp = requests.get(f"https://help.harmanpro.com/{hotfix_page['PageURL']}") 
            soup = BeautifulSoup(page_resp.text, 'html.parser')
            # Get readme to find FGS and associate with a product
            page_readme = soup('div', {"id": "ctl00_PlaceHolderMain_PageContent__ControlWrapper_RichHtmlField"})
            regex = r"(?P<FG>FGN?\d{4}-?\d{0,4}-?[A-Z]{0,2}-?[A-Z]{0,2}-?\d{0,2})\n?\ ?"
            matches = re.finditer(regex, page_readme[0].text, re.MULTILINE)
            for match in matches:
                new_fg, _ = FG.objects.get_or_create(number=match.group().replace(',', '').strip())
                for product in Product.objects.filter(fgs=new_fg):
                    product.associated_names.add(new_name)
                
            download_fields = ["ctl00_PlaceHolderMain_ctl03__ControlWrapper_RichLinkField", "ctl00_PlaceHolderMain_ctl04__ControlWrapper_RichLinkField"]
            try:
                for download in download_fields:
                    download_link = soup("div", {"id": download})[0]("div")[0].find("a")['href']
                    regex = r"_[v,V]?(?P<version>\d{1,3}[\.,_]\d{1,3}[\.,_]?\d{0,8}-?\d?).*\.zip"
                    version_number = re.search(regex, download_link).group('version')
                    
                    if version_number is None:
                        print(f"Unable to get a version number! {download_link}")
                        return
                    version_number = version_number.replace("_", ".")
                    new_version, created = Version.objects.get_or_create(name=f"{hotfix_page['Title']}", number=version_number)
                    new_version.download_page = f"https://help.harmanpro.com{hotfix_page['PageURL']}"
                    new_version.download_url = f"https://help.harmanpro.com{download_link}"
                    new_version.hotfix = True
                    new_version.date_last_seen = timezone.now()
                    new_version.save()

                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Created: {new_version.name}'))
                        new_found_firmwares.append(new_version)

                    # Don't print anything if the firmware already exists...
                    # else:
                    #     self.stdout.write(self.style.NOTICE(f'Already Exists: {new_version.name}'))

            except (IndexError, TypeError):
                pass
            except Exception as error:
                pass

        ### Check for AMX.com updates
        brand = Brand.objects.get(name='AMX')
        for product in Product.objects.filter(brand=brand):
            headers = {'user-agent': 'FirmwareTracker'}
            corrected_name = product.name.replace('/', '-').replace(' ', '-')
            url = f"{brand.base_url}/en-US/products/{corrected_name}"
            response = requests.get(url, headers=headers)
            
            new_versions = self.parse_page(response.text, brand, product)
            if not new_versions:
                continue
            for version in new_versions:
                new_found_firmwares.append(version)

        self.send_emails(new_found_firmwares)

    def parse_page(self, html: str, brand: Brand, product: Product):
        new_versions = []
        # self.stdout.write(self.style.SUCCESS(f'Parsing {product.name} for firmware'))
        cap = Captured()
        soup = BeautifulSoup(html, 'html.parser')
        try:
            rows = soup.body.table("tr")
        except TypeError:
            # This probably means the page doesn't exist or something is different
            # self.stdout.write(self.style.WARNING(f"Unable to parse, brand: {brand.name}, product: {product.name}"))
            return None
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
            # self.stdout.write(self.style.WARNING(f"Unable find specs for, brand: {brand.name}, product: {product.name}"))
            return None
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
                new_version, created = Version.objects.get_or_create(number=version.version_number,
                                                                     name=version.name,
                                                                     download_page=version.download_page,
                                                                     download_url=f"https://www.amx.com{version.download_page}/download")

                for fg in cap.fgs:
                    new_fg, _ = FG.objects.get_or_create(number=fg)
                    new_version.fgs.add(new_fg)
                    product.fgs.add(new_fg)                             
                new_version.date_last_seen = timezone.now()

                new_version.save()

                if created:
                    # We have a new firmware
                    new_versions.append(new_version)


                new_a_name, _ = AssociatedName.objects.get_or_create(name=version.name)
                product.associated_names.add(new_a_name)
            
            product.save()
            return new_versions
        except IntegrityError:
            print(f"got an error on {product}")
            return None
            


    def send_emails(self, new_found_firmwares):
        ### Email updates
        for sub in SubscribedUser.objects.all():
            my_name = "Firmware Finder"
            firmware_html = ""
            for firmware in new_found_firmwares:
                firmware_html = firmware_html + f"<li>{firmware.name} --> {firmware.number}</li>"
            
            if firmware_html == "":
                content = f"""
                Dear {sub.name},</br>
                </br>
                I didn't find any firmware today :(</br>
                </br>
                Thanks,</br>
                Turkish Johnny!</br>
                """
            else:
                content = f"""
                Dear {sub.name},</br>
                </br>
                I found new firmware today!</br>
                <ul>
                    {firmware_html}
                </ul>
                </br>
                Thanks,</br>
                Turkish Johnny!</br>
                """

            msg = MailerMessage()
            msg.subject = "Updated Firmwares"
            msg.to_address = sub.email

            # For sender names to be displayed correctly on mail clients, simply put your name first
            # and the actual email in angle brackets 
            # The below example results in "Dave Johnston <dave@example.com>"
            msg.from_address = '{} <{}>'.format(my_name, 'firmware_finder@ornear.com')

            # As this is only an example, we place the text content in both the plaintext version (content) 
            # and HTML version (html_content).
            msg.content = content
            msg.html_content = content
            msg.save()