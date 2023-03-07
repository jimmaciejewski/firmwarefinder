
from django.test import TestCase
from ..management.commands.check_for_firmware_updates import Command
from bs4 import BeautifulSoup

import re

class RegexTest(TestCase):

    examples = {'SW2106_NX-X200_Master_v1_6_205.zip': '1_6_205',
                'SW2106_NX-X200_Master_v1_4_90.zip': '1_4_90',
                '3535/Hotfix_SW1010-512-0X_DX-RX-4K60_v1.8.3.2.zip': '1.8.3.2',
                '3535/Hotfix_SW1010-312-0X_DX-TX-4K60_v1.8.3.2.zip': '1.8.3.2',
                'EnovaDGX_3.8.25+MCPU-image.zip': '3.8.25',
                'SW2106_NX-X200_Controller_v1_8_120.zip': '1_8_120',
                'AVX-400-SP_v2_5.zip': '2_5',
                'CTP-1301_V5_0_20190820.zip': '5_0_20190820',
                'EnovaDGX_2.2.12-1.zip': '2.2.12-1',
                'SW1906_25A_SWITCHER_v1_9_9.zip': '1_9_9',
                '922/wap1000_9.7.1_firmwareupgrade.zip': '9.7.1',
                '977/N1x33A_Updater_2023-02-02-v1.15.61.zip': '1.15.61',
                '2608/G5SupportFiles%201.5.65.exe.zip': '1.5.65',
                '850/SW0148_11B_MIOR3_v3_08.tsk': '3_08',
                '836/Build%203_01_47.zip': '3_01_47',
                '3246/PR-WP-412_v2.11.zip': '2.11',
                '807/RMS%20Transporter%201.2.25.zip': '1.2.25',
                '2712/N24xx_Updater_2023-02-08-v1.5.119_build1285.zip': '1.5.119',
                'N2xx2A_Updater_2023-02-02-v1.15.61.zip': '1.15.61'}
                

    tricky_examples = {'3034/N-AbleSetup_x64_2023-02-06.zip': '2023-02-06',
                       '3721/N-Command_postSN297_Update_Services_02-14-2018.zip': '02-14-2018',
                       '3173/N3510_Updater_2017_01_06.zip': '2017_01_06'}
                

    # Things I'm not even going to try, we will put exceptions in the code for these:
    # Pass on pdf files
    # '755/Schoolview%20version%208.5.96%20files.pdf': '8.5.86',
    # '770/Schoolview%20version%209.1.37%20files.pdf': '9.1.37',

    # Old product
    # '2607/CPRMS1078.zip': '1078'
    # '950/7in%20Touch%20Panel.zip': '', 

    # Pass on awx files
    # '2858/ZRC%20with%20Room%20Controls.AXW': ''   

    def test_simple_examples(self):
        for key in self.examples:
            regex = r"([_,-]|%20|[v,V])(?P<version>(\d{1,3}[\.,_]){1,}\d{0,8}-?\d).*\.(zip|tsk)"
            result = re.search(regex, key)
            if not hasattr(result, 'group'):
                print(key)
            self.assertEquals(result.group('version'), self.examples[key])

    def test_tricky_examples(self):
        for key in self.tricky_examples:
            regex = r"_(?P<version>(\d{2,4}[_,-]\d{2}[_,-]\d{2,4})).*\.zip"
            result = re.search(regex, key)
            if not hasattr(result, 'group'):
                print(key)
            self.assertEquals(result.group('version'), self.tricky_examples[key])



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


    def test_get_version_number_from_download_field(self):
        '''Given a download field and html creates a version'''
        from .html_examples import n1x33_updater
        soup = BeautifulSoup(n1x33_updater, 'html.parser')
        download_fields = ["ctl00_PlaceHolderMain_ctl03__ControlWrapper_RichLinkField", "ctl00_PlaceHolderMain_ctl04__ControlWrapper_RichLinkField"]
        version_number = Command.get_version_number_from_download_field(None, soup, download_fields[0])
        self.assertEqual(version_number, '1.15.57')
        version_number = Command.get_version_number_from_download_field(None, soup, download_fields[1])
        self.assertEqual(version_number, '1.15.61')


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

