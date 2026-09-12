import datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone

from django_password_manager.models import UserPasswordHistory
from django_password_manager.password_validators import PasswordHistoryValidator

User = get_user_model()


class PasswordHistoryValidatorTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="john",
            email="john@example.com",
            password="CurrentPassword123!",
        )

        self.validator = PasswordHistoryValidator(
            history_size_days_before=31,
        )

    def test_validate_does_nothing_when_user_is_none(self):
        self.validator.validate("AnyPassword123!", user=None)

    def test_validate_does_nothing_for_user_without_pk(self):
        user = User(
            username="john",
            email="john@example.com",
        )
        self.validator.validate("AnyPassword123!", user=user)

    def test_validate_raises_error_when_password_was_used_in_history(self):
        self.user.set_password("OldPassword123!")
        old_password_hash = self.user.password

        UserPasswordHistory.objects.create(
            user=self.user,
            password_hash=old_password_hash,
        )

        with self.assertRaises(ValidationError) as context:
            self.validator.validate("OldPassword123!", user=self.user)
        self.assertEqual(context.exception.code, "password_reused")

    def test_validate_accepts_password_that_was_not_used_before(self):
        self.user.set_password("OldPassword123!")

        UserPasswordHistory.objects.create(
            user=self.user,
            password_hash=self.user.password,
        )
        self.validator.validate("CompletelyNewPassword123!", user=self.user)

    def test_validate_ignores_password_history_older_than_configured_limit(self):
        self.user.set_password("OldPassword123!")
        old_password_hash = self.user.password

        password_history = UserPasswordHistory.objects.create(
            user=self.user,
            password_hash=old_password_hash,
        )

        UserPasswordHistory.objects.filter(
            pk=password_history.pk,
        ).update(
            created_at=timezone.now() - datetime.timedelta(days=32),
        )

        self.validator.validate("OldPassword123!", user=self.user)

    def test_validate_rejects_password_used_within_configured_limit(self):
        self.user.set_password("OldPassword123!")

        password_history = UserPasswordHistory.objects.create(
            user=self.user,
            password_hash=self.user.password,
        )

        UserPasswordHistory.objects.filter(
            pk=password_history.pk,
        ).update(
            created_at=timezone.now() - datetime.timedelta(days=30),
        )

        with self.assertRaises(ValidationError) as context:
            self.validator.validate("OldPassword123!", user=self.user)
        self.assertEqual(context.exception.code, "password_reused")

    def test_validate_uses_custom_history_size(self):
        validator = PasswordHistoryValidator(history_size_days_before=7)
        self.user.set_password("OldPassword123!")
        password_history = UserPasswordHistory.objects.create(
            user=self.user,
            password_hash=self.user.password,
        )

        UserPasswordHistory.objects.filter(
            pk=password_history.pk,
        ).update(
            created_at=timezone.now() - datetime.timedelta(days=8),
        )

        validator.validate("OldPassword123!", user=self.user)

    def test_validate_checks_multiple_password_history_entries(self):
        passwords = [
            "FirstPassword123!",
            "SecondPassword123!",
            "ThirdPassword123!",
        ]

        for password in passwords:
            self.user.set_password(password)
            UserPasswordHistory.objects.create(
                user=self.user,
                password_hash=self.user.password,
            )

        for password in passwords:
            with self.subTest(password=password):
                with self.assertRaises(ValidationError) as context:
                    self.validator.validate(
                        password,
                        user=self.user,
                    )
                self.assertEqual(context.exception.code, "password_reused")

    def test_get_help_text_contains_history_size(self):
        validator = PasswordHistoryValidator(history_size_days_before=31)
        help_text = validator.get_help_text()
        self.assertIn("31", help_text)
        self.assertIn("password", help_text.lower())

    def test_default_history_size_is_taken_from_settings(self):
        with override_settings(PASSWORD_HISTORY_DAYS_LIMIT=14):
            validator = PasswordHistoryValidator()
        self.assertEqual(validator.history_size_days_before, 14)
