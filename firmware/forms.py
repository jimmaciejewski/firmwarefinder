from django.forms import ModelForm
from .models import SubscribedUser


class SubscribeForm(ModelForm):
    class Meta:
        model = SubscribedUser
        fields = ['email', 'name']

