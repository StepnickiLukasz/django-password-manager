import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import UserPasswordHistory

User = get_user_model()


@receiver(post_save, sender=User)
def user_password_drop_to_history(sender, instance, created, **kwargs):
    days_to_expire = getattr(settings, "PASSWORD_DEFAULT_DAYS_TO_EXPIRE")
    pass_obj, created = UserPasswordHistory.objects.get_or_create(
        user_id=instance.pk,
        password_hash=instance.password,
        defaults={"expires_at": (timezone.now() + datetime.timedelta(days=days_to_expire)) if days_to_expire else None},
    )
    #  cleaning expired history objects only if we are sure, the fresh object exists
    if created:
        pass_days_limit = getattr(settings, "PASSWORD_HISTORY_DAYS_LIMIT", 31)
        limit_day = timezone.now() - datetime.timedelta(days=pass_days_limit)
        UserPasswordHistory.objects.filter(
            user_id=instance.pk,
            created_at__lt=limit_day,
        ).delete()
