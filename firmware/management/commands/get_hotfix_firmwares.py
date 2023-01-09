from django.core.management.base import BaseCommand, CommandError
from firmware.models import Brand, Product, FG, Version, AssociatedName, SubscribedUser

import requests
from dataclasses import dataclass, field
import json
import re
from bs4 import BeautifulSoup
from mailqueue.models import MailerMessage

class Command(BaseCommand):
    help = 'Scrapes all products from Harman Hotfix page'

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
                    new_version.save()

                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Created: {new_version.name}'))
                        new_found_firmwares.append(new_version)

                    else:
                        self.stdout.write(self.style.NOTICE(f'Already Exists: {new_version.name}'))

            except (IndexError, TypeError):
                pass
            except Exception as error:
                pass

        ### Email updates
        for sub in SubscribedUser.objects.all():
            my_name = "Firmware Finder"
            firmware_names = [firmware.name for firmware in new_found_firmwares]
            content = f"""
            Dear {sub.name},

            I found new firmware today!
            {firmware_names}

            Thanks,
            Turkish Johnny!
            """

            msg = MailerMessage()
            msg.subject = "Updated Firmwares"
            msg.to_address = sub.email

            # For sender names to be displayed correctly on mail clients, simply put your name first
            # and the actual email in angle brackets 
            # The below example results in "Dave Johnston <dave@example.com>"
            msg.from_address = '{} <{}>'.format(my_name, sub.email)

            # As this is only an example, we place the text content in both the plaintext version (content) 
            # and HTML version (html_content).
            msg.content = content
            msg.html_content = content
            msg.save()
                    
            




