from http import HTTPStatus

from rest_framework import filters, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import BadRequest
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from djoser.views import UserViewSet
from djoser.serializers import SetPasswordSerializer

from .filters import RecipeFilter
from .permissions import IsAuthorAdminOrReadOnly
from .pagination import CustomPagination
from .serializers import (CustomUserCreateSerializer, CustomUserSerializer,
                          IngredientSerializer, FavouriteSerializer,
                          FollowSerializer, TagSerializer,
                          RecipeCreateSerializer, RecipeSerializer)
from recipes.models import (Ingredient, IngredientInRecipe, Favourite,
                            Follow, Recipe, ShoppingList, Tag, User)


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    pagination_class = CustomPagination
    http_method_names = ['get', 'post', 'delete']

    def get_serializer_class(self):
        if self.action in ['subscriptions', 'subscribe']:
            return FollowSerializer
        if self.action == 'create':
            return CustomUserCreateSerializer
        if self.action == 'set_password':
            return SetPasswordSerializer
        return CustomUserSerializer

    @action(['GET'], detail=False, url_path='me',
            permission_classes=(permissions.IsAuthenticated,))
    def me(self, request):
        self.get_object = self.get_instance
        return self.retrieve(request)

    @action(['GET'], detail=False, url_path='subscriptions',
            permission_classes=(permissions.IsAuthenticated,))
    def subscriptions(self, request):
        serializer = self.get_serializer(
            self.paginate_queryset(request.user.follower.all()),
            many=True
        )
        return self.get_paginated_response(serializer.data)

    @action(['POST', 'DELETE'], detail=True, url_path='subscribe',
            permission_classes=(permissions.IsAuthenticated,))
    def subscribe(self, request, id):
        subscription = self.get_object()
        follow_obj = Follow.objects.filter(user=request.user,
                                           subscription=subscription)
        if request.method == 'DELETE':
            if follow_obj.exists():
                follow_obj.delete()
                return Response(status=HTTPStatus.NO_CONTENT)
            raise BadRequest(
                'Ошибка отписки. Вы не подписаны на пользователя.'
            )
        if subscription == request.user:
            raise BadRequest('Невозможно подписаться на самого себя!')
        if follow_obj.exists():
            raise BadRequest('Вы уже подписаны на этого пользователя!')
        follow_obj = Follow.objects.create(
            user=self.request.user, subscription=subscription
        )
        return Response(self.get_serializer(follow_obj).data,
                        status=HTTPStatus.CREATED)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    permission_classes = (IsAuthorAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['create', 'partial_update']:
            return RecipeCreateSerializer
        if self.action in ['favorite', 'shopping_cart']:
            return FavouriteSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def check_and_create_or_delete(self, request, model,
                                   text_err):
        recipe = self.get_object()
        obj = model.objects.filter(user=request.user, recipe=recipe)
        if request.method == 'DELETE':
            if obj.exists():
                obj.delete()
                return Response(status=HTTPStatus.NO_CONTENT)
            raise BadRequest(f'Этого рецепта нет в {text_err},'
                             'его невозможно удалить.')
        if obj.exists():
            raise BadRequest(f'Рецепт уже есть в {text_err}!')
        model.objects.create(user=request.user, recipe=recipe)
        return Response(self.get_serializer(recipe).data,
                        status=HTTPStatus.CREATED)

    @action(['POST', 'DELETE'], detail=True, url_path='favorite',
            permission_classes=(permissions.IsAuthenticated,))
    def favorite(self, request, pk):
        return self.check_and_create_or_delete(
            request, Favourite, 'избранном'
        )

    @action(['POST', 'DELETE'], detail=True, url_path='shopping_cart',
            permission_classes=(permissions.IsAuthenticated,))
    def shopping_cart(self, request, pk):
        return self.check_and_create_or_delete(
            request, ShoppingList, 'списке покупок'
        )

    @action(['GET'], detail=False, url_path='download_shopping_cart',
            permission_classes=(permissions.IsAuthenticated,))
    def download_shopping_cart(self, request):
        recipes_in_shopping_cart = self.queryset.filter(
            is_in_shopping_cart__user=request.user
        )
        lst = {}
        for recipe in recipes_in_shopping_cart:
            for ingredient in recipe.ingredients.all():
                ingredient_in_recipe = IngredientInRecipe.objects.get(
                    recipe=recipe, ingredient=ingredient
                )
                if ingredient.name not in lst:
                    lst[ingredient.name] = ingredient_in_recipe.amount
                else:
                    lst[ingredient.name] += ingredient_in_recipe.amount
        shopping_list_for_txt = 'Список покупок:\n'
        for name, amount in lst.items():
            shopping_list_for_txt += f'{name} - {amount}\n'
        response = HttpResponse(shopping_list_for_txt, headers={
            'Content-Type': 'application/txt',
            'Content-Disposition': 'attachment; filename="shopping_cart.txt"',
        })
        return response
