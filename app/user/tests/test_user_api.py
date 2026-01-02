from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test User',
        }

        res = self.client.post(CREATE_USER_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_create_user_with_existing_email_error(self):
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test User',
        }

        # Create initial user
        create_user(**payload)

        # Attempt to create duplicate user
        res = self.client.post(CREATE_USER_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        payload = {
            'email': 'test@example.com',
            'password': 'pw123',  # too short
            'name': 'Test User',
        }

        res = self.client.post(CREATE_USER_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Ensure user was not created
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_user_token_success(self):
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test User',
        }
        create_user(**payload)

        res = self.client.post(TOKEN_URL, {
            'email': payload['email'],
            'password': payload['password']
        }, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('token', res.data)

    def test_create_token_invalid_credentials(self):
        create_user(email='test@example.com', password='correctpass', name='Test') # noqa

        res = self.client.post(TOKEN_URL, {
            'email': 'test@example.com',
            'password': 'wrongpass'
        }, format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)

    def test_create_token_nonexistent_user(self):
        res = self.client.post(TOKEN_URL, {
            'email': 'nouser@example.com',
            'password': 'testpass123'
        }, format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)

    def test_create_token_blank_password(self):
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test User',
        }
        create_user(**payload)

        # Attempt login with blank password
        res = self.client.post(TOKEN_URL, {
            'email': payload['email'],
            'password': ''
        }, format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)

    def test_retrieve_user_unauthorized(self):
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    def setUp(self):
        self.user = create_user(
            email='user@example.com',
            password='testpass123',
            name='Test User'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_user_success(self):
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['email'], self.user.email)
        self.assertEqual(res.data['name'], self.user.name)

    def test_post_method_not_exists(self):
        res = self.client.post(ME_URL, {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_only_authenticated_user_data_returned(self):
        other_user = create_user(
            email='other@example.com',
            password='otherpass123',
            name='Other User'
        )

        # Even with another user in DB, endpoint returns only self.user data
        res = self.client.get(ME_URL)
        self.assertEqual(res.data['email'], self.user.email)
        self.assertNotEqual(res.data['email'], other_user.email)

    def test_retrieve_user_response_structure(self):
        res = self.client.get(ME_URL)
        self.assertIn('email', res.data)
        self.assertIn('name', res.data)
        self.assertNotIn('password', res.data)  # password must never be returned # noqa

    def test_update_authenticated_user(self):
        payload = {
            'name': 'Test User New',
            'password': 'testnewpass123'
        }
        res = self.client.patch(ME_URL, payload, format='json')
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
