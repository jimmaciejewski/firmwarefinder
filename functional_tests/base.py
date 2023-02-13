from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver


import time

MAX_WAIT = 10

class FunctionalTest(StaticLiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()
        self.browser.maximize_window()


    def tearDown(self):
        self.browser.quit()
