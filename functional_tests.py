from selenium import webdriver
from selenium.webdriver.common.by import By
import unittest


class NewVisitorTest(unittest.TestCase):

    def setUp(self):
        self.browser = webdriver.Chrome()
        self.browser.maximize_window()

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

        # She clicks on discontinued and sees discontinued products
        self.browser.get('http://localhost:8000/discontinued-products')
        self.browser.implicitly_wait(10) # seconds
        products_div = self.browser.find_element(By.ID, 'products-div')  
        products = products_div.find_elements(By.CLASS_NAME, 'discontinued-firmware')
        self.assertGreater(len(products), 0)

        # The firmware versions are in two groups, release firmware in numeric order

        # And hotfix firmware in numeric order

        # When she clicks on a firmware version it expands and shows the readme file

        # When she clicks on the download button it takes her to the correct webpage

        # When she clicks on the product name, it contracts and shows all the products
        # It also highlights the last selected products

        # Edith wonders if she can be notified of updates, and clicks register 
        self.browser.get('http://localhost:8000/register')

        # She is presented with a page that shows user registration
        assert "Register" in self.browser.page_source

        # She try to create an account, but finds out she is a robot...
        elem = self.browser.find_element(By.NAME, 'username')
        elem.send_keys('edith2')
        elem = self.browser.find_element(By.NAME, 'email')
        elem.send_keys('edith@ornear.com')
        elem = self.browser.find_element(By.NAME, 'password1')
        elem.send_keys('letmein!!')
        elem = self.browser.find_element(By.NAME, 'password2')
        elem.send_keys('letmein!!')
        elem = self.browser.find_element(By.XPATH, '/html/body/div[1]/form/button')
        elem.click()
        self.browser.implicitly_wait(10) # seconds
        assert "You need to prove you are not a robot!" in self.browser.page_source

        # She remembers she already has an account and clicks login
        elem = self.browser.find_element(By.LINK_TEXT, 'login')
        elem.click()
        assert "Login" in self.browser.page_source

        # She enters her username and password but gets an error
        elem = self.browser.find_element(By.NAME, 'username')
        elem.send_keys('edith')
        elem = self.browser.find_element(By.NAME, 'password')
        elem.send_keys('wrong password')
        elem = self.browser.find_element(By.XPATH, '/html/body/div/form/button')
        elem.click()
        self.browser.implicitly_wait(10)
        assert "Please try again." in self.browser.page_source

        # She clicks lost password and sees the Reset password page
        elem = self.browser.find_element(By.XPATH, '/html/body/div/p/a')
        elem.click()
        assert "Reset Password" in self.browser.page_source

        # She remembers her password and goes back to the login page
        self.browser.get("http://localhost:8000/accounts/login/")
        elem = self.browser.find_element(By.NAME, 'username')
        elem.send_keys('edith')
        elem = self.browser.find_element(By.NAME, 'password')
        elem.send_keys('letmein!!')
        elem = self.browser.find_element(By.XPATH, '/html/body/div/form/button')
        elem.click()
        assert "edith" in self.browser.page_source

        # She takes a look at her profile
        self.browser.get("http://localhost:8000/profile")
        assert "Profile" in self.browser.page_source

        # She checks the Thanks page is there
        self.browser.get("http://localhost:8000/thanks")
        assert "Thanks for subscribing!" in self.browser.page_source

        # She checks the activate user page is there
        self.browser.get("activate-user/1/")


        # Satisfied, she goes back to sleep


if __name__ == '__main__':
    unittest.main()
