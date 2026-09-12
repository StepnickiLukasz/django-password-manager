from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from django_password_manager.actions import (
    expire_passwords,
    expire_users_passwords,
    generate_password_and_send,
)
from django_password_manager.models import UserPasswordHistory

User = get_user_model()


class PasswordActionsTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="john",
            email="john@example.com",
            password="OldPassword123!",
        )

    def test_expire_users_passwords_expires_only_latest_password(self):
        old_password = UserPasswordHistory.objects.create(
            user=self.user,
            password_hash="old-hash",
        )
        latest_password = UserPasswordHistory.objects.create(
            user=self.user,
            password_hash="latest-hash",
        )
        self.assertIsNone(old_password.expires_at)
        self.assertIsNone(latest_password.expires_at)

        queryset = User.objects.filter(pk=self.user.pk)
        expire_users_passwords(None, None, queryset)
        old_password.refresh_from_db()
        latest_password.refresh_from_db()
        self.assertIsNone(old_password.expires_at)
        self.assertIsNotNone(latest_password.expires_at)

    @patch("django_password_manager.actions.EmailMultiAlternatives")
    @patch("django_password_manager.actions.generate_password")
    def test_generate_password_and_send_changes_password_and_sends_email(
        self,
        mock_generate_password,
        mock_email,
    ):
        generated_password = "GeneratedPassword123"
        mock_generate_password.return_value = generated_password
        queryset = User.objects.filter(pk=self.user.pk)
        generate_password_and_send(None, None, queryset)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(generated_password))
        self.assertFalse(self.user.check_password("OldPassword123!"))

        new_password_history = self.user.password_history.order_by("-created_at").first()
        self.assertIsNotNone(new_password_history)
        self.assertIsNotNone(new_password_history.expires_at)
        mock_generate_password.assert_called_once()
        mock_email.assert_called_once()
        email_instance = mock_email.return_value
        email_instance.attach_alternative.assert_called_once()
        email_instance.send.assert_called_once()
        email_kwargs = mock_email.call_args.kwargs

        self.assertEqual(email_kwargs["to"], [self.user.email])
        self.assertIn(generated_password, email_kwargs["body"])

    def test_expire_passwords_expires_all_selected_passwords(self):
        first_password = UserPasswordHistory.objects.create(
            user=self.user,
            password_hash="first-hash",
        )
        second_password = UserPasswordHistory.objects.create(
            user=self.user,
            password_hash="second-hash",
        )
        queryset = UserPasswordHistory.objects.filter(pk__in=[first_password.pk, second_password.pk])

        expire_passwords(None, None, queryset)
        first_password.refresh_from_db()
        second_password.refresh_from_db()

        self.assertIsNotNone(first_password.expires_at)
        self.assertIsNotNone(second_password.expires_at)

    def test_expire_passwords_does_not_modify_password_hash(self):
        password_history = UserPasswordHistory.objects.create(
            user=self.user,
            password_hash="original-hash",
        )
        queryset = UserPasswordHistory.objects.filter(pk=password_history.pk)
        expire_passwords(None, None, queryset)
        password_history.refresh_from_db()
        self.assertEqual(password_history.password_hash, "original-hash")
        self.assertIsNotNone(password_history.expires_at)
