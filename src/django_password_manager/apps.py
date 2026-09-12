from django.apps import AppConfig


class DjangoPasswordManagerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_password_manager"

    def ready(self):
        from django.contrib import admin
        from django.contrib.auth import get_user_model
        from django.utils.translation import gettext as _

        from django_password_manager.actions import expire_users_passwords, generate_password_and_send

        from . import signals  # noqa

        User = get_user_model()
        model_admin = admin.site._registry.get(User)
        if model_admin:
            original_get_actions = model_admin.get_actions

            def get_actions(request):
                actions = original_get_actions(request)
                actions["expire_passwords"] = (
                    expire_users_passwords,
                    "expire_passwords",
                    _("Expire selected users' passwords"),
                )
                actions["generate_password_and_send"] = (
                    generate_password_and_send,
                    "generate_password_and_send",
                    _("Generate new password and send it by email"),
                )
                return actions

            model_admin.get_actions = get_actions
