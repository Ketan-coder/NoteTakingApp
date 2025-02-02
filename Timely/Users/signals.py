from django.db.models.signals import post_save, pre_delete
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile
from django.utils import timezone
from Notes.models import Notebook, StickyNotes, Remainder

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

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
