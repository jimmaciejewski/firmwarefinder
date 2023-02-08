from django.forms import ModelForm

from django.contrib.auth.models import User
from django.template.loader import render_to_string

from django.core.mail import send_mail

# class SubscribeForm(ModelForm):
#     class Meta:
#         model = User
#         fields = ['email', 'name']

#     def save(self, commit=True):
#         new_user = super(SubscribeForm, self).save(commit=commit)
#         if commit:
#             # Send an email for verification
#             for staff_user in User.objects.filter(is_staff=True):
#                 context = {'name': staff_user.username, 'new_user': new_user}
#                 content = render_to_string(
#                     template_name="firmware/subscription_verification_email.html",
#                     context=context
#                 )
#                 send_mail(
#                     subject="New Subscriber Request",
#                     message=content,
#                     from_email="Firmware Finder <firmware_finder@ornear.com>",
#                     recipient_list=[staff_user.email],
#                     html_message=content
#                 )



class ActivateUserForm(ModelForm):
    class Meta:
        model = User
        fields = ['is_active']


class UserProfileForm(ModelForm):
    class Meta:
        model = User
        fields = ['email']