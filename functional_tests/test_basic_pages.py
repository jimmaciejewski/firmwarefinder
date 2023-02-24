from .base import FunctionalTest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

class BasicPagesTest(FunctionalTest):
    fixtures = ['user.json', 'subscriber.json', 'firmware.json']

    def test_can_get_to_home_page(self):
        # Edith has heard about a cool new online firmware page. She goes
        # to check out its homepage
        self.browser.get(self.live_server_url)

        # She notices the page title and header mention AMX Firmware
        self.assertIn('AMX Firmware', self.browser.title)
        
    
    def test_can_see_current_products(self):
        self.browser.get(self.live_server_url)
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
        elem = self.browser.find_element(By.XPATH, '/html/body/div/div[2]/div[2]/div/ul')
        elem.click()

        # When she clicks on the download button it takes her to the correct webpage

        # When she clicks on the product name, it contracts and shows all the products
        # It also highlights the last selected products

        # She clicks on discontinued and sees discontinued products
        self.browser.get(self.live_server_url + "/discontinued-products")
        self.browser.implicitly_wait(10) # seconds
        products_div = self.browser.find_element(By.ID, 'products-div')  
        products = products_div.find_elements(By.CLASS_NAME, 'discontinued-firmware')
        self.assertGreater(len(products), 0)


       

    def test_registration(self):

        self.browser.get(self.live_server_url)
        # Edith wonders if she can be notified of updates, and clicks register 
        elem = self.browser.find_element(By.LINK_TEXT, 'Sign Up')
        elem.click()

        # She is presented with a page that shows user registration
        assert "Register" in self.browser.page_source

        # She sees the following fields
        try:
            self.browser.find_element(By.NAME, 'first_name')
            self.browser.find_element(By.NAME, 'last_name')
            self.browser.find_element(By.NAME, 'password1')
            self.browser.find_element(By.NAME, 'password2')     
        except NoSuchElementException as error:
            self.assertEqual("", str(error))


    def test_account_creation(self):
        self.browser.get(self.live_server_url)
        elem = self.browser.find_element(By.LINK_TEXT, 'Sign Up')
        elem.click()

        # She try to create an account, but finds out she is a robot...
        elem = self.browser.find_element(By.NAME, 'first_name')
        elem.send_keys('Edith')
        elem = self.browser.find_element(By.NAME, 'last_name')
        elem.send_keys('Doe')
        elem = self.browser.find_element(By.NAME, 'email')
        elem.send_keys('edith@ornear.com')
        elem = self.browser.find_element(By.NAME, 'password1')
        elem.send_keys('letmein!!')
        elem = self.browser.find_element(By.NAME, 'password2')
        elem.send_keys('letmein!!')

        WebDriverWait(self.browser, 10).until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR,"iframe[name^='a-'][src^='https://www.google.com/recaptcha/api2/anchor?']")))
        WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//span[@id='recaptcha-anchor']"))).click()
        self.browser.switch_to.default_content()

        elem = self.browser.find_element(By.XPATH, '/html/body/div[1]/form/button')
        self.browser.execute_script("arguments[0].scrollIntoView();", elem)

        elem.click()
        assert "You will receive an email when your account is activated" in self.browser.page_source


    def test_account_login(self):
        self.browser.get(self.live_server_url)
        elem = self.browser.find_element(By.LINK_TEXT, 'Sign Up')
        elem.click()
        # She remembers she already has an account and clicks login
        elem = self.browser.find_element(By.LINK_TEXT, 'login')
        elem.click()
        assert "Login" in self.browser.page_source

        # She enters her username and password but gets an error
        elem = self.browser.find_element(By.NAME, 'email')
        elem.send_keys('edith@example.com')
        elem = self.browser.find_element(By.NAME, 'password')
        elem.send_keys('wrong password')
        elem = self.browser.find_element(By.XPATH, '/html/body/div/form/button')
        elem.click()
        self.browser.implicitly_wait(10)
        assert "Email or password is not correct" in self.browser.page_source

        # She clicks lost password and sees the Reset password page
        elem = self.browser.find_element(By.XPATH, '/html/body/div/p/a')
        elem.click()
        assert "Reset Password" in self.browser.page_source

    def test_login_to_server(self):
        # She remembers her password and goes back to the login page
        self.browser.get(self.live_server_url + "/login")
        elem = self.browser.find_element(By.NAME, 'email')
        elem.send_keys('edith@example.com')
        elem = self.browser.find_element(By.NAME, 'password')
        elem.send_keys('letmein!!')
        elem = self.browser.find_element(By.XPATH, '/html/body/div/form/button')
        elem.click()
        assert "Email or password is not correct" not in self.browser.page_source
        

    def test_can_see_profile(self):
        self.browser.get(self.live_server_url + "/login")
        elem = self.browser.find_element(By.NAME, 'email')
        elem.send_keys('edith@example.com')
        elem = self.browser.find_element(By.NAME, 'password')
        elem.send_keys('letmein!!')
        elem = self.browser.find_element(By.XPATH, '/html/body/div/form/button')
        elem.click()
        # She takes a look at her profile
        self.browser.get(self.live_server_url + "/profile")
        self.browser.implicitly_wait(10)
        assert "Profile" in self.browser.page_source
        assert "Send an email when firmware updates are found" in self.browser.page_source

        # She checks the Thanks page is there
        self.browser.get(self.live_server_url + "/thanks")
        self.browser.implicitly_wait(10)
        assert "Thanks for subscribing!" in self.browser.page_source
        assert "You will receive an email when your account is activated" in self.browser.page_source
        self.browser.implicitly_wait(10)



    def test_user_activation(self):
        self.browser.get(self.live_server_url + "/login")
        elem = self.browser.find_element(By.NAME, 'email')
        elem.send_keys('edith@example.com')
        elem = self.browser.find_element(By.NAME, 'password')
        elem.send_keys('letmein!!')
        elem = self.browser.find_element(By.XPATH, '/html/body/div/form/button')
        elem.click()
        assert "edith" in self.browser.page_source
        # She checks the activate user page is there
        self.browser.get(self.live_server_url + "/activate-user/4/")

        # She isn't an admin, so she should get the login page
        assert "Activate" not in self.browser.page_source
        assert "Your account doesn't have access to this page." in self.browser.page_source

        # She logs in as an admin
        elem = self.browser.find_element(By.NAME, 'email')
        elem.send_keys('admin_edith@example.com')
        elem = self.browser.find_element(By.NAME, 'password')
        elem.send_keys('letmein!!')
        elem = self.browser.find_element(By.XPATH, '/html/body/div/form/button')
        elem.click()

        assert "Activate User" in self.browser.page_source
        assert "Username" in self.browser.page_source

        # Satisfied, she goes back to sleep
