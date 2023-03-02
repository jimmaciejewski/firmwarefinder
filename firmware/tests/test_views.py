from django.urls import resolve
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.contrib import auth

from ..forms import NewUserForm
from ..views import ProductSearchView, register_request
from ..models import Brand, FG, AssociatedName, Product, upload_path_name, upload_location, Version, Subscriber
from django.core import mail


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
        
        self.assertInHTML('Thanks for subscribing!', response.content.decode())
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


class TestResetPassword(TestCase):

    def test_clicking_reset_password_sends_email(self):
        response = self.client.get('/accounts/password_reset/')
        self.assertInHTML('Reset Password', response.content.decode())
        
    def test_submit_password_reset(self):
        response = self.client.post('/accounts/password_reset/', {'email': 'test@example.com'})
        self.assertRedirects(response, '/accounts/password_reset/done/', status_code=302, target_status_code=200, fetch_redirect_response=True)


class TestActivateUser(TestCase):

    def test_activating_a_user(self):
        admin_user = User.objects.create(username="test admin", email="test@example.com", is_active=True, is_staff=True)
        admin_user.set_password('letmein!!')
        admin_user.save()
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.username == "test admin")
        self.assertTrue(admin_user.email == "test@example.com")
        response = self.client.post("/login", {'email': 'test@example.com',
                                               'password': 'letmein!!'})
        self.assertNotIn("Email or password is not correct", response.content.decode())
        user = auth.get_user(self.client)

        self.assertTrue(user.is_authenticated)

        new_user = User.objects.create(username="test user", email="testuser@example.com")

        response = self.client.get(f'/activate-user/{new_user.id}')
        self.assertInHTML('Activate User', response.content.decode())

        response = self.client.post(f'/activate-user/{new_user.id}', {'is_active': True})
        self.assertInHTML(f'Thanks for activating!', response.content.decode())
        self.assertInHTML(f'You have helped out {new_user.email}', response.content.decode())


class TestNavBar(TestCase):

    def test_nav_bar_has_admin_link_when_admin_logged_in(self):
        response = self.client.get("/")
        self.assertNotContains(response, '<a class="nav-link" aria-current="page" href="/admin">Admin</a>', html=True)
        admin_user = User.objects.create(username="test admin", email="test@example.com", is_active=True, is_staff=True)
        admin_user.set_password('letmein!!')
        admin_user.save()
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.username == "test admin")
        self.assertTrue(admin_user.email == "test@example.com")
        response = self.client.post("/login", {'email': 'test@example.com',
                                               'password': 'letmein!!'})
        self.assertNotIn("Email or password is not correct", response.content.decode())
        user = auth.get_user(self.client)

        self.assertTrue(user.is_authenticated)
        response = self.client.get("/")
        self.assertContains(response, '<a class="nav-link" aria-current="page" href="/admin">Admin</a>', html=True)
