from django.urls import resolve
from django.test import TestCase, RequestFactory
from django.http import HttpRequest


from .views import ProductSearchView  


class HomePageTest(TestCase):


    def test_product_page_returns_correct_html(self):
        request = RequestFactory().get('/')
        view = ProductSearchView(discontinued=False)
        view.setup(request)

        context = view.get_context_data(context_object_name='products')
        self.assertIn('active', context)

