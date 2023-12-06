
from django.test import TestCase
from ..management.commands.check_for_firmware_updates import Command
from bs4 import BeautifulSoup
# import re
import os


class RegexTest(TestCase):

    def test_regex_download_link(self):
        with open(os.path.join('firmware_finder', 'firmware', 'tests', 'version_regex_examples.txt'), 'r') as f:
            for line in f.readlines():
                # Ignore blank and header lines
                if line.strip() == '' or "Solution" in line:
                    continue
                download_link, correct_version = line.split()
                if correct_version == 'None':
                    correct_version = None
                version_number = Command.regex_download_link(None, download_link)
                self.assertEqual(version_number, correct_version)

    def test_regex_all_downloads(self):
        '''I've added this so we check that any changes to regex doesn't break any existing versions'''
        with open(os.path.join('firmware_finder', 'firmware', 'tests', 'all_version_regex_examples.txt'), 'r') as f:
            for line in f.readlines():
                # Ignore blank and header lines
                if line.strip() == '' or "Solution" in line:
                    continue
                download_link, correct_version = line.split()
                if correct_version == 'None':
                    correct_version = None
                version_number = Command.regex_download_link(None, download_link)
                self.assertEqual(version_number, correct_version)


class GetFirmwareDownloadURLfromHARMAN(TestCase):
    def test_get_download_url_from_harman(self):
        from .html_examples import harman_download_page
        soup = BeautifulSoup(harman_download_page, 'html.parser')
        # download_url = Command.get_firmware_values_from_html_table(None, soup)
        download_fields = ["ctl00_PlaceHolderMain_ctl03__ControlWrapper_RichLinkField", "ctl00_PlaceHolderMain_ctl04__ControlWrapper_RichLinkField"]
        for download_field in download_fields:
            download_link = Command.get_download_link_from_download_field(None, soup, download_field)
        self.assertEqual("/Documents/2522/SW2106_NX-X200_Master_v1_6_205.zip", download_link)


class GetFirmwareDownloadURLfromAMX(TestCase):
    # Given the test HTML get the download URL 
    def test_get_download_url_from_soup(self):
        from .html_examples import amx_download_page
        soup = BeautifulSoup(amx_download_page, 'html.parser')
        download_url = Command.get_file_download_url_from_amx_download_page(None, soup)
        self.assertEqual("https://adn.harmanpro.com/softwares/wares/879_1531421958/SW1906_DVX-x2xx_Switcher_v1_7_81.zip", download_url)


class GetPageTitleFromHarman(TestCase):
    def test_get_page_name_from_soup(self):
        from .html_examples import amx_download_page
        soup = BeautifulSoup(amx_download_page, 'html.parser')
        download_url = Command.getpage(None, soup)
        self.assertEqual("https://adn.harmanpro.com/softwares/wares/879_1531421958/SW1906_DVX-x2xx_Switcher_v1_7_81.zip", download_url)


class CheckFirmwareTest(TestCase):

    # Given a hotfix url we need to do the following
    # Download the page

    # Get or create an associated name
    # Get or create FG's that are listed on the page
    #  # Regex FGs
    # Get or create versions on page
    # Link FGs to versions
    # send email to subscribers about new versions

    def test_parse_hotfix_page(self):
        """Should return a list of Versions"""
        pass

    def test_get_title_from_hotfix_page_soup(self):
        """Should return the title of the Hotfix page"""
        from .html_examples import harman_download_page
        soup = BeautifulSoup(harman_download_page, 'html.parser')
        title = Command.get_title_from_hotfix_page(None, soup)
        self.assertEqual(title, "DVX X2XX Switcher Web Page Flash Fix")

    def test_get_fgs_from_hotfix_page_soup(self):
        from .html_examples import harman_download_page
        soup = BeautifulSoup(harman_download_page, 'html.parser')
        readme = Command.get_readme_from_hotfix_page(None, soup)
        self.assertEqual(len(readme[0].text), 3568)


    def test_create_fgs_from_readme(self):
        '''Given some HTML get FGS from readme'''
        from .html_examples import page_readme
        fgs = Command.create_fgs_from_readme(None, read_me=page_readme)
        self.assertEqual(len(fgs), 4)
        self.assertEqual(fgs[0].number, 'FGN1133-SA')

        page_readme = ''
        fgs = Command.create_fgs_from_readme(None, read_me=page_readme)
        self.assertEqual(len(fgs), 0)

    # def test_get_links_from_hotfix_page(self):
    #     from .html_examples import harman_download_page
    #     soup = BeautifulSoup(harman_download_page, 'html.parser')
    #     links = Command.get_links_from_hotfix_page(None, soup)
    #     self.assertEqual(links, 3568)


    def test_get_download_link_from_download_field(self):
        '''Given a download field and html creates a version'''
        from .html_examples import n1x33_updater
        soup = BeautifulSoup(n1x33_updater, 'html.parser')
        download_fields = ["ctl00_PlaceHolderMain_ctl03__ControlWrapper_RichLinkField", "ctl00_PlaceHolderMain_ctl04__ControlWrapper_RichLinkField"]
        download_link = Command.get_download_link_from_download_field(None, soup, download_fields[0])
        self.assertEqual(download_link, '/UnpublishedDocuments/976/N1x33A_Updater_2022-10-27-v1.15.57.zip')
        download_link = Command.get_download_link_from_download_field(None, soup, download_fields[1])
        self.assertEqual(download_link, '/DocumentsInternal/AMX/SVSI/N1x33_Updater_2023-02-02-v1.15.61.zip')

    def test_get_fgs_from_specs_table(self):
        from .html_examples import nx1200
        soup = BeautifulSoup(nx1200, 'html.parser')
        fgs = Command.get_fgs_from_specs_table(None, soup)
        self.assertEqual(fgs, ['FG2106-01'])

    def test_get_firmware_values_from_html_table(self):
        from .html_examples import nx1200
        soup = BeautifulSoup(nx1200, 'html.parser')
        firmwares = Command.get_firmware_values_from_html_table(None, soup)
        self.assertEqual(firmwares, [('NX Series (X200) NX/DVX/DGX Device Firmware',
                                      '1.1.48',
                                      '/en-US/softwares/nx-series-x200-nx-dvx-dgx-device-firmware-v1-1-48'),
                                     ('NX Series (X200) NX/MCP/DGX Controller Firmware',
                                      '1.6.179',
                                      '/en-US/softwares/nx-series-x200-nx-mcp-dgx-controller-firmware-v1-6-179')])

    # def test_get_firmware_values_from_html_software_table(self):
    #     # import requests
    #     # from firmware.models import Brand
    #     # brand, created = Brand.objects.get_or_create(name='AMX', base_url="https://www.amx.com")
    #     # headers = {'user-agent': 'FirmwareTracker'}
    #     # corrected_name = "VARIA-SL50".replace('/', '-').replace(' ', '-')
    #     # url = f"{brand.base_url}/en-US/products/{corrected_name}"
    #     # response = requests.get(url, headers=headers)
    #     from .html_examples import varia
    #     soup = BeautifulSoup(varia, 'html.parser')
    #     firmwares = Command.get_firmware_values_from_html_table(None, soup)
    #     self.assertEqual(firmwares, [('Varia Touch Panel Firmware',
    #                                   '1.11.7',
    #                                   '/en-US/softwares/varia-touch-panel-firmware-v1-11-7')])