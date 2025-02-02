import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notebook, Page, Activity, Remainder

@receiver(post_save, sender=Notebook)
def update_time_notebook(sender, instance, created, **kwargs):
    if not created:  # Only update if the instance already exists
        instance.updated_at += datetime.timedelta(hours=5, minutes=30)
        Notebook.objects.filter(id=instance.id).update(updated_at=instance.updated_at)
        # instance.is_accessed_recently = True
        # instance.save()
    else:
        instance.updated_at += datetime.timedelta(hours=5, minutes=30)
        instance.save()

@receiver(post_save, sender=Page)
def update_time_page(sender, instance, created, **kwargs):
    if not created:
        instance.updated_at += datetime.timedelta(hours=5, minutes=30)
        Page.objects.filter(id=instance.id).update(updated_at=instance.updated_at)
        related_notebook = Notebook.objects.get(id=instance.notebook.id)
        related_notebook.is_accessed_recently = True
        related_notebook.save()
    else:
        instance.updated_at += datetime.timedelta(hours=5, minutes=30)
        instance.save()

@receiver(post_save, sender=Remainder)
def update_time_remainder(sender, instance, created, **kwargs):
    if not created:
        instance.updated_at += datetime.timedelta(hours=5, minutes=30)
        Remainder.objects.filter(id=instance.id).update(updated_at=instance.updated_at)
    else:
        instance.updated_at += datetime.timedelta(hours=5, minutes=30)
        instance.save()

@receiver(post_save, sender=Activity)
def update_time_activity(sender, instance, created, **kwargs):
    if not created:
        instance.updated_at += datetime.timedelta(hours=5, minutes=30)
        Activity.objects.filter(id=instance.id).update(updated_at=instance.updated_at)
    else:
        instance.updated_at += datetime.timedelta(hours=5, minutes=30)
        instance.save()
