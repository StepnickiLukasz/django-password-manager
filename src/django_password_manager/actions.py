import secrets
import string

from django.conf import settings
from django.contrib import admin
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext as _


def generate_password(length=12):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


@admin.action(description=_("Expire selected users' passwords"))
def expire_users_passwords(modeladmin, request, queryset):
    for user in queryset:
        last_password = user.password_history.filter(user=user).order_by("-created_at").first()
        if last_password:
            last_password.expires_at = timezone.now()
            last_password.save(update_fields=["expires_at"])


@admin.action(description=_("Generate new password and send it by email"))
def generate_password_and_send(modeladmin, request, queryset):
    for user in queryset:
        password_length = getattr(settings, "GENERATE_START_PASSWORD_LENGTH")
        password = generate_password(length=password_length)

        user.set_password(password)
        user.save(update_fields=["password"])
        new_pass_obj = user.password_history.order_by("-created_at").first()
        new_pass_obj.expires_at = timezone.now()
        new_pass_obj.save()

        context = {
            "applicationName": getattr(settings, "APPLICATION_NAME"),
            "applicationUrl": getattr(settings, "APPLICATION_URL"),
            "supportEmail": getattr(settings, "SUPPORT_EMAIL"),
            "userName": user.username,
            "temporaryPassword": password,
        }
        text_content = render_to_string("emails/password.txt", context=context)
        html_content = render_to_string("emails/password.html", context=context)
        msg = EmailMultiAlternatives(
            subject=getattr(settings, "EMAIL_SUBJECT", "Twoje hasło tymczasowe"),
            body=text_content,
            from_email=getattr(settings, "EMAIL_FROM", "from@example.com"),
            to=[user.email],
            headers=getattr(settings, "EMAIL_HEADERS", {}),
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()


@admin.action(description=_("Expire selected passwords"))
def expire_passwords(modeladmin, request, queryset):
    queryset.update(expires_at=timezone.now())
