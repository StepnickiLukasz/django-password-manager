from datetime import timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from django_password_manager.middleware import PasswordHistoryManagerMiddleware
from django_password_manager.models import UserPasswordHistory

User = get_user_model()


class UserPasswordDropToHistorySignalTests(TestCase):

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="JohnDoe",
            password="TestPassword",
        )

    @patch("django_password_manager.middleware.redirect")
    def test_does_not_redirect_when_password_is_not_expired(self, mock_redirect):
        request = self.factory.get("/some-url/")
        request.user = self.user
        middleware = PasswordHistoryManagerMiddleware(lambda request: "response")

        response = middleware(request)
        mock_redirect.assert_not_called()
        self.assertEqual(response, "response")

    @patch("django_password_manager.middleware.redirect")
    def test_redirect_if_password_expired(self, mock_redirect):
        self.user.password_history.all().update(expires_at=timezone.now() - timedelta(days=1))
        request = self.factory.get("/some-url/")
        request.user = self.user
        middleware = PasswordHistoryManagerMiddleware(lambda request: "response")
        middleware(request)
        password_change_url = reverse("admin:password_change")
        mock_redirect.assert_called_once_with(password_change_url)

    @patch("django_password_manager.middleware.redirect")
    def test_redirects_user_without_password_history(self, mock_redirect):
        self.user.password_history.all().delete()

        request = self.factory.get("/some-url/")
        request.user = self.user

        middleware = PasswordHistoryManagerMiddleware(lambda request: "response")
        middleware(request)

        mock_redirect.assert_called_once_with(reverse("admin:password_change"))

    def test_force_to_change_password_returns_false_when_password_is_not_expired(self):
        middleware = PasswordHistoryManagerMiddleware(lambda request: "response")
        UserPasswordHistory.objects.create(
            user=self.user,
            password_hash="password-hash",
            expires_at=timezone.now() + timedelta(days=30),
        )
        self.assertFalse(middleware.force_to_change_password(self.user))

    def test_force_to_change_password_returns_true_when_password_is_expired(self):
        middleware = PasswordHistoryManagerMiddleware(lambda request: "response")
        UserPasswordHistory.objects.create(
            user=self.user,
            password_hash="password-hash",
            expires_at=timezone.now() - timedelta(days=1),
        )
        self.assertTrue(middleware.force_to_change_password(self.user))

    @patch("django_password_manager.middleware.redirect")
    def test_does_not_redirect_when_already_on_password_change_page(self, mock_redirect):
        password_change_url = reverse("admin:password_change")
        request = self.factory.get(password_change_url)
        request.user = self.user

        middleware = PasswordHistoryManagerMiddleware(lambda request: "response")
        response = middleware(request)
        mock_redirect.assert_not_called()
        self.assertEqual(response, "response")

    @patch("django_password_manager.middleware.redirect")
    def test_does_not_redirect_anonymous_user(self, mock_redirect):
        request = self.factory.get("/some-url/")
        request.user = AnonymousUser()

        middleware = PasswordHistoryManagerMiddleware(lambda request: "response")
        response = middleware(request)

        mock_redirect.assert_not_called()
        self.assertEqual(response, "response")

    def test_calls_get_response(self):
        get_response = Mock(return_value="response")

        request = self.factory.get("/some-url/")
        request.user = self.user

        middleware = PasswordHistoryManagerMiddleware(get_response)
        middleware(request)

        get_response.assert_called_once_with(request)

    def test_force_to_change_password_returns_false_when_expiration_date_is_none(self):
        middleware = PasswordHistoryManagerMiddleware(lambda request: "response")
        UserPasswordHistory.objects.create(
            user=self.user,
            password_hash="password-hash",
            expires_at=None,
        )
        self.assertFalse(middleware.force_to_change_password(self.user))

    def test_force_to_change_password_uses_latest_password_history(self):
        middleware = PasswordHistoryManagerMiddleware(lambda request: "response")

        UserPasswordHistory.objects.create(
            user=self.user,
            password_hash="old-password",
            expires_at=timezone.now() - timedelta(days=1),
        )

        UserPasswordHistory.objects.create(
            user=self.user,
            password_hash="new-password",
            expires_at=timezone.now() + timedelta(days=30),
        )

        self.assertFalse(middleware.force_to_change_password(self.user))

    @patch("django_password_manager.middleware.redirect")
    def test_returns_redirect_response_when_password_is_expired(self, mock_redirect):
        self.user.password_history.all().update(expires_at=timezone.now() - timedelta(days=1))

        redirect_response = Mock()
        mock_redirect.return_value = redirect_response

        request = self.factory.get("/some-url/")
        request.user = self.user

        middleware = PasswordHistoryManagerMiddleware(lambda request: "response")

        response = middleware(request)

        mock_redirect.assert_called_once_with(reverse("admin:password_change"))
        self.assertIs(response, redirect_response)
