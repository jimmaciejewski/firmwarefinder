from django.forms import ModelForm
from .models import SubscribedUser
from django.contrib.auth.models import User
from django.template.loader import render_to_string

from mailqueue.models import MailerMessage

class SubscribeForm(ModelForm):
    class Meta:
        model = SubscribedUser
        fields = ['email', 'name']

    def save(self, commit=True):
        new_user = super(SubscribeForm, self).save(commit=commit)
        if commit:
            # Send an email for verification
            for staff_user in User.objects.filter(is_staff=True):
                context = {'name': staff_user.username, 'new_user': new_user}
                content = render_to_string(
                    template_name="firmware/subscription_verification_email.html",
                    context=context
                )
                self.add_email_to_queue(staff_user, content)


    def add_email_to_queue(self, subscriber, content):
        my_name = "Firmware Finder"
        msg = MailerMessage()
        msg.subject = "New Subscriber Request"
        msg.to_address = subscriber.email

        # For sender names to be displayed correctly on mail clients, simply put your name first
        # and the actual email in angle brackets 
        # The below example results in "Dave Johnston <dave@example.com>"
        msg.from_address = '{} <{}>'.format(my_name, 'firmware_finder@ornear.com')

        # As this is only an example, we place the text content in both the plaintext version (content) 
        # and HTML version (html_content).
        msg.content = content
        msg.html_content = content
        msg.save()


class ActivateUserForm(ModelForm):
    class Meta:
        model = SubscribedUser
        fields = ['is_active']

