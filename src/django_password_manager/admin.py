from django.contrib import admin

from django_password_manager.actions import expire_passwords
from django_password_manager.models import UserPasswordHistory


class UserPasswordAdmin(admin.ModelAdmin):
    fields = (
        "user",
        "password_hash",
        "created_at",
        "expires_at",
    )
    readonly_fields = (
        "user",
        "password_hash",
        "created_at",
    )
    actions = (expire_passwords,)


admin.site.register(UserPasswordHistory, UserPasswordAdmin)
