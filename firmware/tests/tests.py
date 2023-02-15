from django.urls import resolve
from django.test import TestCase, RequestFactory
from django.http import HttpRequest
from django.core.files.base import File
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.core.management import call_command
from mailer.models import Message
from io import StringIO


from ..views import ProductSearchView  
from ..models import Brand, FG, AssociatedName, Product, upload_path_name, upload_location, Version, Subscriber



# email templates
class EmailTemplateTest(TestCase):

    def create_versions(self):
        test_ver1 = Version.objects.create(name="SVSI N2400 Series Windowing Processor Firmware Updater", number="1.2.3", download_page="/en-US/softwares/svsi-n2400-series-windowing-processor-firmware-updater-v2-2-40", download_url="https://www.amx.com/en-US/softwares/svsi-n2400-series-windowing-processor-firmware-updater-v2-2-40/download")
        test_ver2 = Version.objects.create(name="N2410 SVSI Hotfix firmware Updater", number="3.2.1", download_page="https://help.harmanpro.com/Documents/1502/N2410Update_2022-01-13_v2.2.25.zip", download_url="https://help.harmanpro.com/n2410-window-processor-updater-hotfix", hotfix=True)
        return [test_ver1, test_ver2]

    def test_email_template(self):
        versions = self.create_versions()
        context = {'name': 'jim', 'versions': versions}
        content = render_to_string(template_name="email/updates_email.html", context=context)
    
        self.assertIn('SVSI N2400', content)


    def test_email_contains_failed_searches(self):
        versions = self.create_versions()
        context = {'name': 'jim', 'developer': True, 'versions': versions, "searches": ["2023-02-01T03:20:01.414107+00:00 :: a new failed search", "2023-02-07T00:04:16.678822+00:00 :: asdfasdfasd", "2023-02-07T00:04:45.719079+00:00 :: next failed", "2023-02-07T00:04:47.408940+00:00 :: next failed search", "2023-02-08T02:55:30.895418+00:00 :: failed search on wednesday"]}
        content = render_to_string(template_name="email/updates_email.html", context=context)
        with open("test_email.html", "w") as f:
            f.write(content)


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
