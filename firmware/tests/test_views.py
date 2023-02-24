from django.urls import resolve
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.contrib import auth

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


class TestLogInWithEmail(TestCase):

    def test_login_page_has_email_as_login(self):
        response = self.client.post("/login")
        self.assertInHTML("Email", response.content.decode())

        
    def test_able_to_login_with_email(self):
        new_user = User.objects.create(username="test user", email="test@example.com", is_active=True)
        new_user.set_password('letmein!!')
        new_user.save()
        self.assertTrue(new_user.is_active)
        self.assertTrue(new_user.username == "test user")
        self.assertTrue(new_user.email == "test@example.com")
        response = self.client.post("/login", {'email': 'test@example.com',
                                               'password': 'letmein!!'})
        self.assertNotIn("Email or password is not correct", response.content.decode())
        user = auth.get_user(self.client)

        self.assertTrue(user.is_authenticated)


class TestRedirectsToCorrectLoginPage(TestCase):

    def test_logout_template_redirects_to_login(self):
        response = self.client.get('/accounts/logout/')
        self.assertContains(response, '<a href="/login">Log in again</a>', html=True)