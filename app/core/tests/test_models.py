from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


class ModelTests(TestCase):
    def test_create_user_with_email_successful(self):
        email = 'test@example.com'
        password = 'testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_email_normalization_variants(self):
        samples = [
            ("TEST@EXAMPLE.COM", "TEST@example.com"),
            ("Test@GMAIL.COM", "Test@gmail.com"),
        ]

        for raw, expected in samples:
            user = get_user_model().objects.create_user(
                email=raw,
                password="pass123"
            )
            self.assertEqual(user.email, expected)

    def test_email_is_required(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email=None,
                password="testpass123"
            )

    def test_empty_email_is_invalid(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email="",
                password="testpass123"
            )

    def test_create_superuser_successful(self):
        user = get_user_model().objects.create_superuser(
            email="admin@example.com",
            password="adminpass123"
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_active)

    def test_superuser_must_have_is_staff_true(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_superuser(
                email="admin2@example.com",
                password="adminpass123",
                is_staff=False,
            )

    def test_superuser_must_have_is_superuser_true(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_superuser(
                email="admin3@example.com",
                password="adminpass123",
                is_superuser=False,
            )

    def test_create_recipe(self):
        user = get_user_model().objects.create_user(
            name="Test User",
            email="test@example.com",
            password="testpass123"
        )
        recipe = models.Recipe.objects.create(
            user=user,
            title='Sample Recipe Name',
            time_minutes=5,
            price=Decimal('720'),
            description='Sample recipe description',
        )

        self.assertEqual(str(recipe), recipe.title)
