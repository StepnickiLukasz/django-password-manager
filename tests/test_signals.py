import random
import string

from django.contrib.auth import get_user_model
from django.test import TestCase

from django_password_manager.models import UserPasswordHistory

User = get_user_model()


class UserPasswordDropToHistorySignalTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = User.objects.create()

    def _generate_random_password(self):
        chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
        size = random.randint(16, 32)
        return "".join(random.choice(chars) for _ in range(size))

    def test_new_user_drops_password_to_history(self):
        user = User.objects.create_user(
            first_name="John",
            last_name="Doe",
            email="johndoe@example.com",
            username="JohnDoe",
            password=self._generate_random_password(),
        )
        self.assertTrue(UserPasswordHistory.objects.filter(user=user, password_hash=user.password).exists())

    def test_existing_user_drops_password_to_history(self):
        user = User.objects.create_user(
            first_name="John",
            last_name="Doe",
            email="johndoe@example.com",
            username="JohnDoe",
            password=self._generate_random_password(),
        )
        old_password = user.password
        user.set_password(self._generate_random_password())
        user.save()
        new_password = user.password
        self.assertTrue(UserPasswordHistory.objects.filter(user=user, password_hash=old_password).exists())
        self.assertTrue(UserPasswordHistory.objects.filter(user=user, password_hash=new_password).exists())
