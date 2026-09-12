from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext as _


class UserPasswordHistory(models.Model):

    class Meta:
        ordering = ["-created_at"]

    user = models.ForeignKey(
        verbose_name=_("user"),
        related_name="password_history",
        to=get_user_model(),
        on_delete=models.CASCADE,
    )
    password_hash = models.CharField(
        verbose_name=_("password hash"),
        max_length=255,
    )
    created_at = models.DateTimeField(
        verbose_name=_("creataed at"),
        auto_now_add=True,
    )
    expires_at = models.DateTimeField(
        verbose_name=_("expires at"),
        help_text=_(
            "Set the date when the password expires and the user will be required to change it. "
            "Leave empty for a password that never expires."
        ),
        null=True,
    )

    def __str__(self):
        return f"[UserPasswordHistory] user={self.user.username}, hash={self.password_hash}"
