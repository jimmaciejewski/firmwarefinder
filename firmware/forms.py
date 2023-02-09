from django import forms

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import inlineformset_factory

from .models import Subscriber


class ActivateUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['is_active']


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']


class NewUserForm(UserCreationForm):
	email = forms.EmailField(required=True)

	class Meta:
		model = User
		fields = ("username", "email", "password1", "password2")

	def save(self, commit=True):
		user = super(NewUserForm, self).save(commit=False)
		user.email = self.cleaned_data['email']
		if commit:
			user.save()
		return user

class SubscriberForm(forms.ModelForm):
	class Meta:
		model = Subscriber
		fields = ['send_email']
	