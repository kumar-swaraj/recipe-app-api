import os
import tempfile
from decimal import Decimal

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)


RECIPES_URL = reverse('recipe:recipe-list')


def recipe_detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args=[recipe_id])


def image_upload_url(recipe_id):
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


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

    def test_create_recipe_with_tags(self):
        payload = {
            "title": "Thai Prawn Curry",
            "time_minutes": 30,
            "price": Decimal("325.24"),
            "tags": [
                {"name": "Thai"},
                {"name": "Dinner"},
            ]
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload["tags"]:
            exists = Tag.objects.filter(name=tag["name"], user=self.user).exists() # noqa
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        tag_south_indian = Tag.objects.create(user=self.user, name="South Indian") # noqa
        payload = {
            "title": "Pongal",
            "time_minutes": 60,
            "price": Decimal("932.53"),
            "tags": [
                {"name": "Breakfast"},
                {"name": "South Indian"},
                {"name": "Delicious"},
            ]
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 3)
        self.assertIn(tag_south_indian, recipe.tags.all())
        for tag in payload["tags"]:
            exists = Tag.objects.filter(name=tag["name"], user=self.user).exists() # noqa
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        recipe = create_recipe(user=self.user)
        payload = {
            "tags": [
                {"name": "Lunch"},
            ]
        }
        url = recipe_detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name="Lunch")
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        tag_breakfast = Tag.objects.create(user=self.user, name="Breakfast")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name="Lunch")
        payload = {"tags": [{"name": "Lunch"}]}
        url = recipe_detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        tag_breakfast = Tag.objects.create(user=self.user, name="Breakfast")
        tag_lunch = Tag.objects.create(user=self.user, name="Lunch")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        payload = {"tags": []}
        url = recipe_detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertCountEqual(payload["tags"], recipe.tags.all()) # noqa
        self.assertNotIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_create_recipe_with_ingredients(self):
        payload = {
            "title": "Creamy Peanut Butter Shake",
            "time_minutes": 30,
            "price": Decimal("325.24"),
            "ingredients": [
                {"name": "Butter"},
                {"name": "Peanut"},
            ]
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload["ingredients"]:
            exists = Ingredient.objects.filter(name=ingredient["name"], user=self.user).exists() # noqa
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredients(self):
        ingredient_coconut = Ingredient.objects.create(user=self.user, name="Coconut") # noqa
        payload = {
            "title": "Pongal",
            "time_minutes": 60,
            "price": Decimal("932.53"),
            "ingredients": [
                {"name": "Ghee"},
                {"name": "Coconut"},
                {"name": "Lentils"},
            ]
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 3)
        self.assertIn(ingredient_coconut, recipe.ingredients.all())
        for ingredient in payload["ingredients"]:
            exists = Ingredient.objects.filter(name=ingredient["name"], user=self.user).exists() # noqa
            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):
        recipe = create_recipe(user=self.user)
        payload = {
            "ingredients": [
                {"name": "Peanut"},
            ]
        }
        url = recipe_detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(user=self.user, name="Peanut")
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_ingredient(self):
        ingredient_butter = Ingredient.objects.create(user=self.user, name="Butter") # noqa
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient_butter)

        ingredient_peanut = Ingredient.objects.create(user=self.user, name="Peanut") # noqa
        payload = {"ingredients": [{"name": "Peanut"}]}
        url = recipe_detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient_peanut, recipe.ingredients.all())
        self.assertNotIn(ingredient_butter, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        ingredient_butter = Ingredient.objects.create(user=self.user, name="Butter") # noqa
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient_butter)

        payload = {"ingredients": []}
        url = recipe_detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertCountEqual(payload["ingredients"], recipe.ingredients.all()) # noqa
        self.assertNotIn(ingredient_butter, recipe.ingredients.all())


class RecipeImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            name="Test User",
            email="test@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            res = self.client.post(url, {'image': ntf}, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        url = image_upload_url(self.recipe.id)
        res = self.client.post(url, {'image': 'notimage'}, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
