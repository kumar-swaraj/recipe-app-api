from rest_framework import serializers

from core.models import Recipe, Tag, Ingredient


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = [
            "id",
            "name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = [
            "id",
            "name",
            "slug",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = [
            "id",
            "title",
            "slug",
            "price",
            "time_minutes",
            "ingredients",
            "tags",
            "image",
            "link",
        ]
        read_only_fields = ["id", "slug"]

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        ingredients = validated_data.pop("ingredients", [])
        recipe = Recipe.objects.create(**validated_data)
        auth_user = self.context["request"].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag
            )
            recipe.tags.add(tag_obj)

        for ingredient in ingredients:
            ingredient_obj, created = Ingredient.objects.get_or_create(
                user=auth_user,
                **ingredient
            )
            recipe.ingredients.add(ingredient_obj)

        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        ingredients = validated_data.pop("ingredients", None)
        instance = super().update(instance, validated_data)

        if tags is not None:
            auth_user = self.context["request"].user
            instance.tags.clear()

            for tag in tags:
                tag_obj, _ = Tag.objects.get_or_create(
                    user=auth_user,
                    **tag
                )
                instance.tags.add(tag_obj)

        if ingredients is not None:
            auth_user = self.context["request"].user
            instance.ingredients.clear()

            for ingredient in ingredients:
                ingredient_obj, _ = Ingredient.objects.get_or_create(
                    user=auth_user,
                    **ingredient
                )
                instance.ingredients.add(ingredient_obj)

        return instance

    def validate_time_minutes(self, value):
        if value <= 0:
            raise serializers.ValidationError("Time must be greater than zero.") # noqa
        return value


class RecipeDetailSerializer(RecipeSerializer):
    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + [
            "description",
            "created_at",
            "updated_at"
        ]
        read_only_fields = RecipeSerializer.Meta.read_only_fields + ["created_at", "updated_at"] # noqa


class RecipeImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ["id", "image"]
        read_only_fileds = ["id"]
        extra_kwargs = {"image": {"required": True}}
