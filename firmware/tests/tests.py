from django.urls import resolve
from django.test import TestCase, RequestFactory
from django.http import HttpRequest
from django.core.files.base import File
from django.contrib.auth.models import User


from ..views import ProductSearchView  
from ..models import Brand, FG, AssociatedName, Product, upload_path_name, upload_location, Version, Subscriber


# views test
class ThanksTest(TestCase):

    def test_thanks_returns_view(self):
        pass


# models test
class BrandTest(TestCase):

    def create_brand(self, name="BSS", base_url="https://bss.com"):
        return Brand.objects.create(name=name, base_url=base_url)

    def test_brand_creation(self):
        b = self.create_brand()
        self.assertTrue(isinstance(b, Brand))
        self.assertEqual(b.__str__(), b.base_url)

class FGTest(TestCase):

    def create_fg(self, number="1234"):
        return FG.objects.create(number=number)

    def test_fg_creation(self):
        fg = self.create_fg()
        self.assertTrue(isinstance(fg, FG))
        self.assertEqual(fg.__str__(), fg.number)

class AssociatedNameTest(TestCase):

    def create_associated_name(self, name="NX-1200 firmware"):
        return AssociatedName.objects.create(name=name)

    def test_associated_name_creation(self):
        an = self.create_associated_name()
        self.assertTrue(isinstance(an, AssociatedName))
        self.assertEqual(an.__str__(), an.name)

class ProductTest(TestCase):

    def create_product(self, name="NX-1200", brand_name="AMX", brand_url="https://amx.com", fg_number="FG-123", associated_name="NX-1200 firmware", discontinued=False):
        brand_obj = Brand.objects.create(name=brand_name, base_url=brand_url)
        fg_obj = FG.objects.create(number=fg_number)
        associated_name_obj = AssociatedName.objects.create(name=associated_name) 
        product_obj = Product.objects.create(name=name, brand=brand_obj)
        product_obj.fgs.add(fg_obj)
        product_obj.associated_names.add(associated_name_obj)
        product_obj.save()
        return product_obj

    def test_product_creation(self):
        prod = self.create_product()
        self.assertTrue(isinstance(prod, Product))
        self.assertEqual(prod.__str__(), prod.name)
        
    def test_dashless_name_creation(self):
        prod = self.create_product()
        self.assertEqual(prod.create_dashless_associated_name().name, 'NX1200')


class UploadTest(TestCase):

    def test_upload_path_name(self):
        path_name = upload_path_name("DGX x00 with 4K60 DXLink - Switcher & Controller Update-")
        self.assertEqual(path_name, "DGX-x00-with-4K60-DXLink---Switcher---Controller-Update")

    def test_upload_location(self):
        version = Version.objects.create(name="NX Firmware", number="1.6.209")
        location = upload_location(version, "SW1906_25A_SWITCHER_v2_0_0.kit")
        self.assertEqual(location, "NX-Firmware\\SW1906_25A_SWITCHER_v2_0_0.kit")


class VersionTest(TestCase):

    def create_version(self, name="NX-1200 firmware", number="1.6.205"):
        ver = Version.objects.create(name=name, number=number)
        # with open("firmware/tests/SW2106_NX-X200_FakeMaster_v1_6_193.zip", 'r') as f:
        #     ver.local_file.save("SW2106_NX-X200_FakeMaster_v1_6_193.zip", File(f))
        return Version.objects.create(name=name, number=number)

    def test_version_creation(self):
        ver = self.create_version()
        self.assertTrue(isinstance(ver, Version))
        self.assertEqual(ver.__str__(), "NX-1200 firmware v1.6.205")

class SubscriberTest(TestCase):

    def create_subscriber(self, name="Edith"):
        user = User.objects.create(username=name)
        return Subscriber.objects.create(user=user)

    def test_subscriber_creation(self):
        sub = self.create_subscriber()
        self.assertTrue(isinstance(sub, Subscriber))
        self.assertEqual(sub.__str__(), sub.user.username)
