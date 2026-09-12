import datetime

from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext as _


class PasswordHistoryValidator:
    def __init__(self, history_size_days_before=None):
        self.history_size_days_before = history_size_days_before or getattr(settings, "PASSWORD_HISTORY_DAYS_LIMIT", 31)

    def validate(self, password, user=None):
        if user is None or not user.pk:
            return

        from_date = timezone.now() - datetime.timedelta(days=self.history_size_days_before)
        history = user.password_history.filter(created_at__gte=from_date).order_by("-created_at")

        for password_history in history:
            if check_password(password, password_history.password_hash):
                raise ValidationError(
                    _(
                        "The password does not meet the password history requirements. "
                        "Type a password that has not been used previously."
                    ),
                    code="password_reused",
                )

    def get_help_text(self):
        return _("The password cannot be the same as one you have used " "within the last %(days)s days.") % {
            "days": self.history_size_days_before
        }
