from django.db.models.signals import post_save, pre_delete
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile
from django.utils import timezone
from Notes.models import Notebook, StickyNotes, Remainder
from rest_framework.authtoken.models import Token
from Notes.utils import send_email
import uuid

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        profile = Profile.objects.create(user=instance, firstName=instance.first_name, lastName=instance.last_name, email=instance.email, email_confirmation_token=uuid.uuid4())
        Token.objects.create(user=instance)
        send_email(
            to_email=instance.email,
            subject="Confirm Your Email",
            title="Confirm Email",
            body=f"Hi {instance.username}, click the button below to verify your email.",
            anchor_link=f"https://timely.pythonanywhere.com/accounts/confirm/{profile.email_confirmation_token}/",            
            anchor_text="Confirm Email"
        )

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()

@receiver(pre_delete, sender=User)
def delete_profile(sender, instance, **kwargs):
    instance.profile.delete()

@receiver(post_save, sender=Profile)
def create_dummy_notebook(sender, instance, created, **kwargs):
    if created:
        Notebook.objects.create(title="Dummy Notebook", body="Dummy Notebook Body", author=instance)
        StickyNotes.objects.create(title="Dummy Sticky Note", body="Dummy Sticky Note Body", author=instance)
        Remainder.objects.create(title="Dummy Remainder", body="Dummy Remainder Body",alert_time=timezone.now()+ timezone.timedelta(hours=6), author=instance)

@receiver(post_save, sender=Profile)
def save_dummy_notebook(sender, instance, **kwargs):
    if hasattr(instance, 'notebook'):
        instance.notebook.save()
    if hasattr(instance, 'sticky_notes'):
        instance.sticky_notes.save()
    if hasattr(instance, 'remainder'):
        instance.remainder.save()
