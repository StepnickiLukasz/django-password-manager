from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone


class PasswordHistoryManagerMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
        self._cache = {}

    def __call__(self, request):
        if request.user and not request.user.is_anonymous:
            if self.force_to_change_password(request.user):
                password_change_url = reverse("admin:password_change")
                if request.path != password_change_url:
                    return redirect(password_change_url)
        response = self.get_response(request)
        return response

    def force_to_change_password(self, user):
        last_password = user.password_history.order_by("-created_at").first()
        if not last_password:
            return True
        return (last_password.expires_at < timezone.now()) if last_password.expires_at else False
