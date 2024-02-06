from itertools import chain

from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe

from .models import (Ingredient, IngredientInRecipe, Favourite, Follow, Recipe,
                     ShoppingList, Tag)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'slug',
    )
    list_filter = ('name', )
    list_display_links = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'measurement_unit',
    )
    list_filter = ('name',)
    list_display_links = ('name',)


class IngredientInline(admin.TabularInline):
    model = IngredientInRecipe


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'author',
        'ingredient_names',
        'recipe_count',
        'pub_date',
    )
    fields = ('author', 'name', 'text', 'image', 'image_preview',
              'tags', 'cooking_time')
    readonly_fields = ('image_preview',)
    list_filter = ('author', 'name', 'tags',)
    list_display_links = ('name',)
    inlines = (IngredientInline,)

    @admin.display(description='Добавлений в избранное')
    def recipe_count(self, obj):
        return obj.is_favorited.count()

    @admin.display(description='Ингредиенты')
    def ingredient_names(self, obj):
        a = obj.ingredients.values_list('name')
        return list(chain.from_iterable(a))

    @admin.display(description='Изображение')
    def image_preview(self, obj):
        return mark_safe(f'<img src={obj.image.url} width="80" height="60">')


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'recipe',
        'ingredient',
        'amount'
    )
    list_filter = ('recipe', 'ingredient',)
    list_display_links = ('ingredient',)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'author'
    )
    list_filter = ('user',)
    list_display_links = ('user',)


@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'recipe'
    )
    list_filter = ('recipe',)
    list_display_links = ('user',)


@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'recipe'
    )
    list_filter = ('recipe',)
    list_display_links = ('user',)


admin.site.unregister(Group)
