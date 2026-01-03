from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext as _

from core import models


@admin.register(models.User)
class UserAdmin(BaseUserAdmin):
    ordering = ['id']
    list_display = ['email', 'name']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {'fields': ('name',)}),
        (
            _('Permissions'), {
                'fields': ('is_active', 'is_staff', 'is_superuser')
            }
        ),
        (_('Important dates'), {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('name', 'email', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser') # noqa
        }),
    )
    readonly_fields = ['last_login']


@admin.register(models.Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "slug",
        "time_minutes",
        "price",
        "created_at",
    )
    list_filter = ("user", "created_at")
    search_fields = ("title", "description", "slug")
    readonly_fields = ("slug", "created_at", "updated_at")
    ordering = ("-created_at",)
    list_select_related = ("user",)
    # prepopulated_fields = {"slug": ("title",)}


@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "user",
        "slug",
        "created_at"
    )
    list_filter = ("user", "created_at")
    search_fields = ("name", "slug")
    readonly_fields = ("slug", "created_at", "updated_at")
    ordering = ("-created_at",)
    list_select_related = ("user",)
