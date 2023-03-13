
from django.test import TestCase
from ..management.commands.check_for_firmware_updates import Command
from bs4 import BeautifulSoup

import re

class RegexTest(TestCase):

    def test_regex_download_link(self):
        import os 
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


class CheckFirmwareTest(TestCase):

    # Given a hotfix url we need to do the following
    # Download the page

    # Get or create an associated name
    # Get or create FG's that are listed on the page
    #  # Regex FGs
    # Get or create versions on page
    # Link FGs to versions
    # send email to subscribers about new versions


    def test_create_fgs_from_readme(self):
        '''Given some HTML get FGS from readme'''
        from .html_examples import page_readme
        fgs = Command.create_fgs_from_readme(None, read_me=page_readme)
        self.assertEqual(len(fgs), 4)
        self.assertEqual(fgs[0].number, 'FGN1133-SA')

        page_readme = ''
        fgs = Command.create_fgs_from_readme(None, read_me=page_readme)
        self.assertEqual(len(fgs), 0)


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