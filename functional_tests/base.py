from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

class FunctionalTest(StaticLiveServerTestCase):

    def setUp(self):

        options = Options()
        options.binary_location = r"C:\\Program Files\\Mozilla Firefox\\firefox.exe"

        self.browser = webdriver.Firefox(options=options)
        self.browser.maximize_window()



    def tearDown(self):
        if True:
            self.browser.quit()
