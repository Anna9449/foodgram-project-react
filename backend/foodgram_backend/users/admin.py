from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import FoodgramUser


@admin.register(FoodgramUser)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'id',
        'username',
        'email',
        'recipe_count',
        'follower_count'
    )
    list_filter = ('username', 'email')
    search_fields = ('username', 'email')
    list_display_links = ('username',)

    @admin.display(description='Кол-во рецептов')
    def recipe_count(self, obj):
        return obj.recipes.count()

    @admin.display(description='Кол-во подписчиков')
    def follower_count(self, obj):
        return obj.author.count()
