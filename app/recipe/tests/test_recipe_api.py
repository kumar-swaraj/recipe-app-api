from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe
from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)


RECIPES_URL = reverse('recipe:recipe-list')


def recipe_detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_user(**params):
    return get_user_model().objects.create_user(**params)


def create_recipe(user, **params):
    defaults = {
        "title": "Sample Recipe Name",
        "description": "Sample recipe description",
        "time_minutes": 22,
        "price": Decimal("560.75"),
        "link": "https://recipe.com/"
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


class PublicRecipeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            name="Test User",
            email="test@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        create_recipe(user=self.user)
        create_recipe(
            user=self.user,
            title="Sample Recipe Name 2",
            price=Decimal('640.32'),
            )

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        user2 = get_user_model().objects.create_user(
            email='other@example.com',
            password='password123'
        )
        create_recipe(user=user2)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        recipe = create_recipe(user=self.user)

        url = recipe_detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe, many=False)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        payload = {
            'title': 'Chocolate cheesecake',
            'time_minutes': 30,
            'price': Decimal('149.24')
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))
        self.assertEqual(recipe.user, self.user)

    def test_partial_update_recipe(self):
        recipe = create_recipe(user=self.user)

        payload = {'title': 'Chicken tikka'}
        url = recipe_detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])

    def test_full_update_recipe(self):
        recipe = create_recipe(user=self.user)
        payload = {
            'title': 'Spaghetti carbonara',
            'time_minutes': 25,
            'price': Decimal('849.44')
        }
        url = recipe_detail_url(recipe.id)
        self.client.put(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.price, payload['price'])

    def test_delete_recipe(self):
        recipe = create_recipe(user=self.user)
        res = self.client.delete(recipe_detail_url(recipe.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_user_recipe_error(self):
        new_user = create_user(email="newuser@example.com", password="newpass123") # noqa
        recipe = create_recipe(user=new_user)

        url = recipe_detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())
