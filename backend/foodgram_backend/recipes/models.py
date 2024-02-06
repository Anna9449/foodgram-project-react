from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from api.const import LENGTH_TEXT_OUTPUT, MAX_LENGTH_INPUT_NAME

User = get_user_model()


class Tag(models.Model):
    name = models.CharField('Название тега', max_length=MAX_LENGTH_INPUT_NAME,
                            unique=True)
    color = ColorField('Цвет тега', unique=True)
    slug = models.SlugField('Слаг', max_length=MAX_LENGTH_INPUT_NAME,
                            unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name[:LENGTH_TEXT_OUTPUT]


class Ingredient(models.Model):
    name = models.CharField('Название ингредиента',
                            max_length=MAX_LENGTH_INPUT_NAME)
    measurement_unit = models.CharField('Единица измерения',
                                        max_length=MAX_LENGTH_INPUT_NAME)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = (
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_name_measurement_unit',
            ),
        )

    def __str__(self):
        return self.name[:LENGTH_TEXT_OUTPUT]


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
        related_name='recipes'
    )
    name = models.CharField('Название', max_length=MAX_LENGTH_INPUT_NAME)
    text = models.TextField('Описание')
    image = models.ImageField('Изображение блюда', upload_to='foodgram/')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )
    cooking_time = models.PositiveIntegerField(
        'Время приготовления',
        validators=[
            MaxValueValidator(1440),
            MinValueValidator(1)
        ],)
    pub_date = models.DateTimeField(
        'Дата публикации', auto_now_add=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name[:LENGTH_TEXT_OUTPUT]


class IngredientInRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.PositiveIntegerField(
        'Количество',
        validators=[
            MaxValueValidator(10000),
            MinValueValidator(1)
        ],)
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Ингридиенты в рецепте'
        verbose_name_plural = 'Ингридиенты в рецептах'
        default_related_name = 'ingredient_in_recipe'
        constraints = (
            models.UniqueConstraint(
                fields=['ingredient', 'recipe'],
                name='unique_ingredient_in_recipe',
            ),
        )

    def __str__(self):
        return self.ingredient.name[:LENGTH_TEXT_OUTPUT]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='author',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author',
            ),
        )

    def __str__(self):
        return self.author.username[:LENGTH_TEXT_OUTPUT]


class FavouriteModel(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Избранный рецепт'
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.recipe.name[:LENGTH_TEXT_OUTPUT]


class Favourite(FavouriteModel):

    class Meta(FavouriteModel.Meta):
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        default_related_name = 'is_favorited'
        constraints = (
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe_in_favorite',
            ),
        )


class ShoppingList(FavouriteModel):

    class Meta(FavouriteModel.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        default_related_name = 'is_in_shopping_cart'
        constraints = (
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe_in_shopping_cart',
            ),
        )
