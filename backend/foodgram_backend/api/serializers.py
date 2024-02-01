import base64

import webcolors
from django.core.files.base import ContentFile
from django.db.models import Count
from djoser.serializers import (TokenCreateSerializer, UserCreateSerializer,
                                UserSerializer)
from rest_framework import serializers

from recipes.models import (Ingredient, IngredientInRecipe, Follow, Recipe,
                            Tag, User)


class Hex2NameColor(serializers.Field):
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError('Для этого цвета нет имени')
        return data


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email',
            'first_name', 'last_name', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        if self.context['request'].user.is_anonymous:
            return False
        if obj == self.context['request'].user:
            return False
        if Follow.objects.filter(user=self.context['request'].user,
                                 subscription=obj):
            return True
        return False


class CustomUserCreateSerializer(UserCreateSerializer):
    password = serializers.CharField(
        max_length=128, write_only=True, required=True
    )
    email = serializers.EmailField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email',
            'first_name', 'last_name', 'password'
        )

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'Пользователь с таким email уже зарегистрирован.'
            )
        return value


class CustomTokenSerializer(TokenCreateSerializer):
    email = serializers.EmailField()
    username = serializers.CharField(required=False)

    def validate(self, attrs):
        attrs["username"] = User.objects.get(email=attrs["email"])
        return super(CustomTokenSerializer, self).validate(attrs)


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
    id = serializers.PrimaryKeyRelatedField(source='ingredient',
                                            queryset=Ingredient.objects.all())
    name = serializers.CharField(
        source='ingredient.name'
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientInRecipeCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')

    def validate_id(self, value):
        if Ingredient.objects.filter(id=value).exists():
            return value
        raise serializers.ValidationError(
            f'Вы добавили несуществующий ингредиент {id}.'
        )

    def validate_amount(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Количество ингредиента не может быть меньше 1.'
            )
        return value


class RecipeSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer()
    tags = TagSerializer(many=True)
    image = Base64ImageField()
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        exclude = ('pub_date',)

    def get_ingredients(self, obj):
        ingredients = IngredientInRecipe.objects.filter(recipe=obj)
        return IngredientInRecipeSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        if self.context['request'].user.is_anonymous:
            return False
        if obj.is_favorited.filter(user=self.context['request'].user).exists():
            return True
        return False

    def get_is_in_shopping_cart(self, obj):
        if self.context['request'].user.is_anonymous:
            return False
        if obj.is_in_shopping_cart.filter(
            user=self.context['request'].user
        ).exists():
            return True
        return False


class RecipeCreateSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = IngredientInRecipeCreateSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        exclude = ('pub_date',)
        read_only_fields = ('pub_date',)

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Время приготовления не может быть меньше 1.'
            )
        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Добавьте в рецепт хотя бы один ингредиент.'
            )
        lst = []
        for ingredient in value:
            if ingredient['id'] in lst:
                dbl_ingredient = ingredient['id']
                raise serializers.ValidationError(
                    f'Повторяющийся ингредиент - {dbl_ingredient}.'
                )
            lst.append(ingredient['id'])
        return value

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

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        for ingredient in ingredients_data:
            current_ingredient = Ingredient.objects.get(id=ingredient['id'])
            IngredientInRecipe.objects.create(ingredient=current_ingredient,
                                              recipe=recipe,
                                              amount=ingredient['amount'])
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)
        instance.image = validated_data.get('image', instance.image)

        if 'tags' not in validated_data:
            raise serializers.ValidationError(
                'Поле тег не должно быть пустым.'
            )
        elif 'ingredients' not in validated_data:
            raise serializers.ValidationError(
                'Поле ингредиентов не должно быть пустым.'
            )
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        instance.tags.set(tags_data)
        lst = []
        for ingredient in ingredients_data:
            current_ingredient = Ingredient.objects.get(id=ingredient['id'])
            lst.append(current_ingredient)
            IngredientInRecipe.objects.get_or_create(
                ingredient=current_ingredient,
                recipe=instance,
                amount=ingredient['amount']
            )
        instance.ingredients.set(lst)
        instance.save()
        return instance

    def to_representation(self, obj):
        return RecipeSerializer(
            obj, context={'request': self.context['request']}
        ).data


class FavouriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(source='subscription',
                                            queryset=User.objects.all())
    username = serializers.CharField(source='subscription.username')
    email = serializers.EmailField(source='subscription.email')
    first_name = serializers.CharField(source='subscription.first_name')
    last_name = serializers.CharField(source='subscription.last_name')
    is_subscribed = serializers.BooleanField(default=True)
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = (
            'id', 'username', 'email', 'first_name',
            'last_name',  'is_subscribed', 'recipes', 'recipes_count')
        read_only_fields = ('user', 'subscription')

    def get_recipes(self, obj):
        recipes = Recipe.objects.filter(author=obj.subscription)
        recipes_limit = (
            self.context['request'].query_params.get('recipes_limit')
        )
        if recipes_limit:
            recipes = recipes[0:int(recipes_limit)]
        return FavouriteSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        recipes = Recipe.objects.filter(author=obj.subscription)
        return recipes.aggregate(Count('id'))['id__count']
