from django.urls import resolve
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User

from ..forms import NewUserForm
from ..views import ProductSearchView, register_request
from ..models import Brand, FG, AssociatedName, Product, upload_path_name, upload_location, Version, Subscriber



# register_request form
class RegisterTest(TestCase):

    def test_register_form(self):
        form_data = {'first_name': 'Test',
                     'last_name': 'Example', 
                     'email': 'test@example.com',
                     'password1': 'letmein!!',
                     'password2': 'letmein!!'}
        form = NewUserForm(data=form_data)
        if not form.is_valid():
            self.assertEqual("", form.error_messages)
        self.assertTrue(form.is_valid())

    def test_register_view(self):
        response = self.client.post("/register", {'first_name': 'Test',
                                                  'last_name': 'Example', 
                                                  'email': 'test@example.com',
                                                  'password1': 'letmein!!',
                                                  'password2': 'letmein!!'})
        
        self.assertRedirects(response, '/thanks/')
        new_user = User.objects.get(username='test.example')
        self.assertEqual(new_user.username, 'test.example')
        self.assertEqual(new_user.first_name, 'Test')
        self.assertEqual(new_user.last_name, 'Example')
