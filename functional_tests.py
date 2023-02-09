from selenium import webdriver
from selenium.webdriver.common.by import By
import unittest


class NewVisitorTest(unittest.TestCase):

    def setUp(self):
        self.browser = webdriver.Chrome()

    def tearDown(self):
        self.browser.quit()

    def test_can_see_a_list_of_products(self):

        # Edith has heard about a cool new online firmware page. She goes
        # to check out its homepage
        self.browser.get('http://localhost:8000')

        # She notices the page title and header mention AMX Firmware
        self.assertIn('AMX Firmware', self.browser.title)

        # She sees a list of current products on the page
        self.browser.implicitly_wait(10) # seconds
        products_div = self.browser.find_element(By.ID, 'products-div')  
        products = products_div.find_elements(By.CLASS_NAME, 'current-firmware')
        self.assertGreater(len(products), 0)

        # She clicks on a product and it shows a list of firmware versions applicable to that product
        products[0].click()


        # The firmware versions are in two groups, release firmware in numeric order

        # And hotfix firmware in numeric order

        # When she clicks on a firmware version it expands and shows the readme file

        # When she clicks on the download button it takes her to the correct webpage

        # When she clicks on the product name, it contracts and shows all the products
        # It also highlights the last selected products

        # Edith wonders if she can be notified of updates, and clicks register 
        self.browser.get('http://localhost:8000/register')

        # She is presented with a page that shows user registration

        # She creates an account, and is shown a profile page that allows her to enable or disable notification emails

        # Satisfied, she goes back to sleep


if __name__ == '__main__':
    unittest.main()
