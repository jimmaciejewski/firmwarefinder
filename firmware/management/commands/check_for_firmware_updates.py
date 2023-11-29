from django.core.management.base import BaseCommand
from firmware.models import Brand, Product, FG, Version, AssociatedName, Subscriber
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.conf import settings

import requests
import json
import re
from bs4 import BeautifulSoup


class Command(BaseCommand):
    help = 'Checks for updates'
    new_found_versions = []

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--test_email',
            action='store_true',
            help='Dont actually check, but send an test email anyway',
        )
        parser.add_argument(
            '--debug',
            action='store_true',
            help='Print extra debug information',
        )
        parser.add_argument(
            '--release_only',
            action='store_true',
            help='Only AMX pages',
        )
        parser.add_argument(
            '--hotfix_only',
            action='store_true',
            help='Only Hotfix pages',
        )
        parser.add_argument(
            '--no_email',
            action='store_true',
            help='Dont send any emails out'
        )

    def handle(self, *args, **options):
        self.debug = options['debug']
        self.no_email = options['no_email']
        if options['test_email']:
            test_ver1 = Version.objects.first()
            test_ver2 = Version.objects.get(name="SVSI N2400 Series Windowing Processor Firmware Updater")
            self.send_emails([test_ver1, test_ver2], testing=True)
            self.send_emails([], testing=True)
            return

        if not options['release_only']:
            url = "https://help.harmanpro.com/_api/web/lists/getbytitle('Pages')/Items?$top=1000&$orderby=Title&$select=PublishingPageContent,PageURL,Title,FileRef,Brand/Title, Brand/ID, Model/Title, Family/Title, DocType/Title,CaseType0/Title,FaultCategory/Title&$expand=Family,Model,CaseType0,Brand,FaultCategory,DocType&$filter=DocType/Title eq 'Hotfix firmware'"
            headers = {'user-agent': 'FirmwareTracker', "accept": "application/json"}
            response = requests.get(url, headers=headers)
            my_json = json.loads(response.text)

            for hotfix_page in my_json['value']:

                if hotfix_page['Brand'][0]['Title'] != 'AMX':
                    continue
                if self.debug:
                    self.stdout.write(self.style.SUCCESS(f"Checking help.harmanpro.com: {hotfix_page['Title']}"))
                new_versions = self.process_hotfix_page(hotfix_page)
                for version in new_versions:
                    self.new_found_versions.append(version)

        if not options['hotfix_only']:
            """Check for AMX.com updates"""
            brand = Brand.objects.get(name='AMX')
            for product in Product.objects.filter(brand=brand):
                if self.debug:
                    self.stdout.write(self.style.SUCCESS(f"Checking amx.com: {product.name}"))
                new_versions = self.parse_amx_page(product)
                for version in new_versions:
                    self.new_found_versions.append(version)

            if self.debug:
                self.stdout.write(self.style.SUCCESS(f"Sending email with updates for: {self.new_found_versions}"))
            self.send_emails(self.new_found_versions)

    def parse_amx_page(self, product: Product) -> list[Version]:
        '''Given a product parse it's amx.com page'''
        created_versions = []
        brand = Brand.objects.get(name='AMX')
        headers = {'user-agent': 'FirmwareTracker'}
        corrected_name = product.name.replace('/', '-').replace(' ', '-')
        url = f"{brand.base_url}/en-US/products/{corrected_name}"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        try:
            firmwares = self.get_firmware_values_from_html_table(soup)
            found_fgs = self.get_fgs_from_specs_table(soup)
        except TypeError:
            # This probably means the page doesn't exist or something is different
            if self.debug:
                self.stdout.write(self.style.WARNING(f"Unable to parse, brand: {brand.name}, product: {product.name}"))
            return created_versions

        for name, version_number, download_page in firmwares:
            # Example download page = "https://www.amx.com/en/softwares/dxlink-transmitter-firmware-v1-6-29"
            # We now need to get the download url
            dlp_response = requests.get(download_page, headers=headers)
            dlp_soup = BeautifulSoup(dlp_response.content, 'html.parser')
            download_url = self.get_file_download_url_from_amx_download_page(dlp_soup)
            new_version, created = Version.objects.get_or_create(name=name,
                                                                 number=version_number,
                                                                 download_page=download_page,
                                                                 download_url=download_url)
            new_version.date_last_seen = timezone.now()
            if created:
                created_versions.append(new_version)

            for fg in found_fgs:
                new_fg, _ = FG.objects.get_or_create(number=fg)
                new_version.fgs.add(new_fg)
                product.fgs.add(new_fg)
            new_version.save()

            new_a_name, _ = AssociatedName.objects.get_or_create(name=new_version.name)
            product.associated_names.add(new_a_name)
            product.save()

        return created_versions

    def process_hotfix_page(self, hotfix_page) -> list[Version]:
        '''Take a hotfix url and create new versions and fgs from the html'''
        created_versions = []
        associated_name, _ = AssociatedName.objects.get_or_create(name=hotfix_page['Title'])
        # download hotfix page
        page_resp = requests.get(f"https://help.harmanpro.com/{hotfix_page['PageURL']}")
        if page_resp.status_code != 200:
            print(f"Unable to read page for https://help.harmanpro.com/{hotfix_page['PageURL']} got a {page_resp.status_code}")
            return created_versions
        soup = BeautifulSoup(page_resp.text, 'html.parser')
        # Get readme to find FGS and associate with a product
        page_readme = soup('div', {"id": "ctl00_PlaceHolderMain_PageContent__ControlWrapper_RichHtmlField"})
        found_fgs = self.create_fgs_from_readme(page_readme[0].text)
        for fg in found_fgs:
            for product in Product.objects.filter(fgs=fg):
                product.associated_names.add(associated_name)
        # Get version files
        download_fields = ["ctl00_PlaceHolderMain_ctl03__ControlWrapper_RichLinkField", "ctl00_PlaceHolderMain_ctl04__ControlWrapper_RichLinkField"]
        for download_field in download_fields:
            download_link = self.get_download_link_from_download_field(soup, download_field)
            if not download_link:
                continue
            version_number = self.regex_download_link(download_link)
            if not version_number:
                print(f"Unable to get a version number! {download_link}")
                continue
            else:
                new_version, created = Version.objects.get_or_create(name=f"{hotfix_page['Title']}",
                                                                     number=version_number,
                                                                     download_page=f"https://help.harmanpro.com{hotfix_page['PageURL']}",
                                                                     download_url=f"https://help.harmanpro.com{download_link}")
                new_version.hotfix = True
                new_version.date_last_seen = timezone.now()
                new_version.save()
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created: {new_version.name} --> {new_version.number}'))
                    created_versions.append(new_version)

        return created_versions
    
    def get_file_download_url_from_amx_download_page(self, soup):
        '''Returns the url to download the firmware from the soup provided'''
        download_url = ""
        try:
            download_url = soup.find_all("a", {"class": "software-direct-link"})[0]['href']
        except Exception as error:
            self.stdout.write(self.style.WARNING("Unable to find the AMX download url."))
        return download_url

    def get_fgs_from_specs_table(self, soup):
        '''Returns fg numbers found in specs table in the soup provided'''
        found_fgs = []
        try:
            rows = soup.body("table", {"class": "specs"})[0]("tr")
        except IndexError:
            if self.debug:
                self.stdout.write(self.style.WARNING("Unable to find FG table."))
            return found_fgs
        for row in rows:
            if "FG Numbers" in row.text:
                regex = r"(?P<FG>FGN?\d{4}-?\d{0,4}-?[A-Z]{0,2}-?[A-Z]{0,2}-?\d{0,2})\n?\ ?"
                matches = re.finditer(regex, row.text, re.MULTILINE)
                for match in matches:
                    found_fgs.append(match.group().replace(',', '').strip())
                else:
                    regex = r"(?P<FG>AMX-\D{2}-\D{2}-\d{3})"
                    matches = re.finditer(regex, row.text, re.MULTILINE)
                    for match in matches:
                        found_fgs.append(match.group().replace(',', '').strip())
        return found_fgs

    def get_firmware_values_from_html_table(self, soup):
        '''Returns a tuple of name version download_page of any firmwares in the html'''
        firmwares = []
        at_firmware = False
        rows = soup.body.table("tr")
        for row in rows:
            if at_firmware and row("h6"):
                # This means we have finished the firmware section
                break
            if at_firmware:
                # This should be a firmware
                # td 0 is the firmware link and name
                name = row("td")[0]("a")[0].text.strip()
                # td 1 is the version
                version_number = row("td")[1].text.strip()
                download_page = row("td")[0]("a")[0].get('href')
                firmwares.append((name, version_number, download_page))
            if "Firmware" in str(row):
                at_firmware = True
        return firmwares

    def get_failed_searches(self):
        failed_searches = []
        try:
            with open('failed_searches.txt', 'r') as f:
                searches = f.read()
                for search in searches.split('\n'):
                    cleaned = search.strip()
                    if cleaned:
                        failed_searches.append(cleaned)
        except Exception as error:
            print(f"Unable to open failed_searches: {error}")
        return failed_searches

    def archive_searches(self):
        try:
            with open('failed_searches.txt', 'r') as f:
                failed_searches = f.read()
            with open('archived_searches.txt', 'a') as f:
                f.write(failed_searches)
            with open('failed_searches.txt', 'w') as f:
                # clear file
                pass
        except Exception as error:
            print(f"Unable to archive_searches: {error}")

    def send_emails(self, new_found_firmwares, testing=False):
        """ Email updates """
        if self.no_email:
            return
        # Create HTML email
        context = {'versions': new_found_firmwares, 'searches': self.get_failed_searches(), 'testing': testing}

        for user in User.objects.filter(is_active=True):
            context['developer'] = user.is_staff
            context['name'] = f"{user.first_name}"
            content = render_to_string(
                template_name="email/updates_email.html",
                context=context
            )

            if testing:
                # if we are testing only send email to staff users
                if user.is_staff:
                    self.add_email_to_queue(user, content)
            else:
                sub = Subscriber.objects.get(user=user)
                # If we have new firmware send it to subs that have requested it
                if new_found_firmwares:
                    if sub.send_email:
                        self.add_email_to_queue(user, content)
                else:
                    # We don't have new firmware send the update to subs that have requested it
                    if sub.send_email_even_if_none_found:
                        self.add_email_to_queue(user, content)
                self.archive_searches()

    def add_email_to_queue(self, user, content):
        send_mail(
            subject="Updated Firmwares",
            message=content,
            from_email=f"Firmware Finder <{settings.DEFAULT_FROM_EMAIL}>",
            recipient_list=[user.email],
            html_message=content
        )

    def create_fgs_from_readme(self, read_me) -> list[FG]:
        '''Given some readme text returns all FG's found'''
        fgs = []
        regex = r"(?P<FG>FGN?\d{4}-?\d{0,4}-?[A-Z]{0,2}-?[A-Z]{0,2}-?\d{0,2})\n?\ ?"
        matches = re.finditer(regex, read_me, re.MULTILINE)
        for match in matches:
            new_fg, _ = FG.objects.get_or_create(number=match.group().replace(',', '').strip())
            fgs.append(new_fg)
        return fgs

    def get_link_from_download_field(self, soup, download_field):
        '''Given a download field parse the soup'''
        pass

    def get_download_link_from_download_field(self, soup, download_field):
        '''Given a download field parse the soup for version numbers'''
        try:
            download_link = soup("div", {"id": download_field})[0]("div")[0].find("a")['href']
            if download_link[-4:] in ['.tsk', '.pdf', '.AXW', '.kit'] or 'CPRMS1078.zip' in download_link or '7in%20Touch%20Panel.zip' in download_link:
                return None
            return download_link

        except TypeError:
            if self.debug:
                if download_field == "ctl00_PlaceHolderMain_ctl04__ControlWrapper_RichLinkField":
                    self.stdout.write(self.style.WARNING('Unable to find second download field'))
                else:
                    self.stdout.write(self.style.WARNING(f'Unable to find download field! {download_field}'))
            return None

    def regex_download_link(self, download_link):
        '''Uses regex to get the version number from a download link'''
        # Strategy regex most likely first, edge cases last check for valid before returning
        # 1. Versions with dots ie v1.14.5
        # 2. Versions with dashes ie v1_14_5
        # 3. Versions with dates ie 2020-10-23 or 23-10-2020
        searches = [r"(v|V|_|-|%20)(?P<version>(\d{1,3}\.){1,}\d{0,8}-?\d).*\.zip",
                    r"(v|V|%20|_)(?P<version>\d_\d{1,3}(_\d{1,8})?).*\.zip",
                    r"_(?P<version>(\d{2,4}[_,-]\d{2}[_,-]\d{2,4})).*\.zip"]
        for i, regex in enumerate(searches):
            matches = re.search(regex, download_link)
            if hasattr(matches, 'group'):
                version_number = matches.group('version')
                if i == 2:
                    # Dates have dashes
                    version_number = version_number.replace("_", "-")
                else:
                    # Clean up versions to have dots
                    version_number = version_number.replace("_", ".")
                return version_number
        return None
