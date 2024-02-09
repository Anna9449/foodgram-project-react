import webcolors
from django.core.validators import MaxValueValidator, MinValueValidator
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from .const import MAX_VALUE, MIN_VALUE
from recipes.models import (Ingredient, IngredientInRecipe, Favourite, Follow,
                            Recipe, ShoppingList, Tag, User)


class Hex2NameColor(serializers.Field):
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError('Для этого цвета нет имени')
        return data


class FoodgramUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email',
            'first_name', 'last_name', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context['request']
        return (request and request.user.is_authenticated
                and obj.author.filter(user=request.user).exists())


class TagSerializer(serializers.ModelSerializer):
    color = Hex2NameColor()

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id', read_only=True,)
    name = serializers.CharField(
        source='ingredient.name', read_only=True,
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True,
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = ('amount',)


class IngredientInRecipeCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        validators=[MaxValueValidator(MAX_VALUE),
                    MinValueValidator(MIN_VALUE)],
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    author = FoodgramUserSerializer()
    tags = TagSerializer(many=True)
    ingredients = IngredientInRecipeSerializer(source='ingredient_in_recipe',
                                               many=True)
    is_favorited = serializers.BooleanField()
    is_in_shopping_cart = serializers.BooleanField()

    class Meta:
        model = Recipe
        exclude = ('pub_date',)


class RecipeCreateSerializer(serializers.ModelSerializer):
    author = FoodgramUserSerializer(read_only=True,)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = IngredientInRecipeCreateSerializer(many=True)
    image = Base64ImageField(allow_null=False, allow_empty_file=False)
    cooking_time = serializers.IntegerField(
        validators=[MaxValueValidator(MAX_VALUE),
                    MinValueValidator(MIN_VALUE)],
    )

    class Meta:
        model = Recipe
        exclude = ('pub_date',)
        read_only_fields = ('pub_date',)

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Добавьте в рецепт хотя бы один тег.'
            )
        if list(set(value)) < value:
            raise serializers.ValidationError(
                'Теги в рецепте не должны повторяться.'
            )
        return value

    def validate(self, data):
        if not data['ingredients']:
            raise serializers.ValidationError(
                'Добавьте в рецепт хотя бы один ингредиент.'
            )
        lst = [ingredient['id'] for ingredient in data['ingredients']]
        if len(lst) > len(set(lst)):
            raise serializers.ValidationError(
                'В рецепте есть повторяющиеся ингредиенты.'
            )
        return data

    def create_ingredient_in_recipe(self, recipe, ingredients_data):
        lst = []
        for ingredient in ingredients_data:
            ingredient_in_recipe_obj = IngredientInRecipe(
                ingredient=ingredient['id'],
                recipe=recipe,
                amount=ingredient['amount']
            )
            lst.append(ingredient_in_recipe_obj)
        IngredientInRecipe.objects.bulk_create(lst)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data,
                                       author=self.context['request'].user)
        recipe.tags.set(tags_data)
        self.create_ingredient_in_recipe(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        instance.tags.set(tags_data)
        instance.ingredient_in_recipe.all().delete()
        self.create_ingredient_in_recipe(instance, ingredients_data)
        lst = [ingredient['id'] for ingredient in ingredients_data]
        instance.ingredients.set(lst)
        return super().update(instance, validated_data)

    def to_representation(self, obj):
        return RecipeSerializer(obj, context=self.context).data


class FavouriteShopListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavouriteShopListCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favourite
        fields = ('user', 'recipe')

    def validate(self, data):
        user = self.context['request'].user
        if self.Meta.model.objects.filter(user=user,
                                          recipe=data['recipe']).exists():
            raise serializers.ValidationError(
                'Рецепт уже есть в списке покупок!'
            )
        return data

    def to_representation(self, obj):
        return FavouriteShopListSerializer(obj.recipe,
                                           context=self.context).data


class FavouriteCreateSerializer(FavouriteShopListCreateSerializer):
    class Meta(FavouriteShopListCreateSerializer.Meta):
        model = Favourite


class ShoppingListCreateSerializer(FavouriteShopListCreateSerializer):
    class Meta(FavouriteShopListCreateSerializer.Meta):
        model = ShoppingList


class FollowSerializer(FoodgramUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(
        source='recipes.count'
    )

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name',
            'last_name', 'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        recipes = obj.recipes.all()
        recipes_limit = (
            self.context['request'].query_params.get('recipes_limit')
        )
        try:
            recipes = recipes[:int(recipes_limit)]
        except None:
            None
        return FavouriteShopListSerializer(recipes, many=True,
                                           context=self.context).data


class FollowCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Follow
        fields = ('user', 'author')

    def validate_author(self, value):
        user = self.context['request'].user
        if value == user:
            raise serializers.ValidationError(
                'Невозможно подписаться на самого себя!'
            )
        if value.author.filter(user=user).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя!'
            )
        return value

    def to_representation(self, obj):
        return FollowSerializer(obj.user, context=self.context).data
