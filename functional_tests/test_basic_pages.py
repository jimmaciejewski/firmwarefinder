# from .base import FunctionalTest
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys


# class BasicPagesTest(FunctionalTest):

#     def test_can_get_to_home_page(self):
#         # Edith has heard about a cool new online firmware page. She goes
#         # to check out its homepage
#         self.browser.get(self.live_server_url)

#         # She notices the page title and header mention AMX Firmware
#         self.assertIn('AMX Firmware', self.browser.title)
        
    
#     def test_can_see_current_products(self):
#         self.browser.get(self.live_server_url)
#         # She sees a list of current products on the page
#         self.browser.implicitly_wait(10) # seconds
#         products_div = self.browser.find_element(By.ID, 'products-div')  
#         products = products_div.find_elements(By.CLASS_NAME, 'current-firmware')
#         self.assertGreater(len(products), 0)

#         # She clicks on a product and it shows a list of firmware versions applicable to that product
#         products[0].click()

#         # She clicks on discontinued and sees discontinued products
#         self.browser.get(self.live_server_url + '/discontinued-products')
#         self.browser.implicitly_wait(10) # seconds
#         products_div = self.browser.find_element(By.ID, 'products-div')  
#         products = products_div.find_elements(By.CLASS_NAME, 'discontinued-firmware')
#         self.assertGreater(len(products), 0)