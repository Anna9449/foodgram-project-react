from django.contrib import admin

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


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'author',
        'recipe_count',
        'pub_date'
    )
    list_filter = ('author', 'name', 'tags',)
    list_display_links = ('name',)

    @admin.display(description='Кол-во добавлений рецепта в избранное')
    def recipe_count(self, obj):
        return obj.is_favorited.count()


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
        'subscription'
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
