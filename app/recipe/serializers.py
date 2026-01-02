from rest_framework import serializers

from core.models import Recipe


class RecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = [
            "id",
            "title",
            "slug",
            "time_minutes",
            "price",
            "link",
        ]
        read_only_fields = ["id", "slug"]


class RecipeDetailSerializer(RecipeSerializer):
    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + [
            "description",
            "created_at",
            "updated_at"
        ]
        read_only_fields = RecipeSerializer.Meta.read_only_fields + ["created_at", "updated_at"] # noqa

    def validate_time_minutes(self, value):
        if value <= 0:
            raise serializers.ValidationError("Time must be greater than zero.") # noqa
        return value
