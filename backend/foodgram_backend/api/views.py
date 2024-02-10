from http import HTTPStatus

from django.db.models import Exists, OuterRef, Sum
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import filters, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import RecipeFilter
from .pagination import CustomPagination
from .permissions import IsAuthorAdminOrReadOnly
from .serializers import (IngredientSerializer, FavouriteCreateSerializer,
                          FollowSerializer, FoodgramUserSerializer,
                          FollowCreateSerializer, RecipeCreateSerializer,
                          RecipeSerializer, TagSerializer,
                          ShoppingListCreateSerializer)
from recipes.models import (Ingredient, IngredientInRecipe, Favourite, Follow,
                            Recipe, ShoppingList, Tag, User)


class FoodgramUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = FoodgramUserSerializer
    pagination_class = CustomPagination
    http_method_names = ('get', 'post', 'delete')

    def get_permissions(self):
        if self.action == 'me':
            return (permissions.IsAuthenticated(),)
        return super().get_permissions()

    @action(['GET'], detail=False, url_path='subscriptions',
            permission_classes=(permissions.IsAuthenticated,))
    def subscriptions(self, request):
        serializer = FollowSerializer(
            self.paginate_queryset(
                User.objects.filter(author__user=request.user)
            ),
            many=True, context=self.get_serializer_context()
        )
        return self.get_paginated_response(serializer.data)

    @action(['POST'], detail=True, url_path='subscribe',
            permission_classes=(permissions.IsAuthenticated,))
    def subscribe(self, request, id):
        serializer = FollowCreateSerializer(
            data={'user': request.user.id,
                  'author': id},
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=HTTPStatus.CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        follow_obj = Follow.objects.filter(user=request.user,
                                           author__id=id)
        if follow_obj.exists():
            follow_obj.delete()
            return Response(status=HTTPStatus.NO_CONTENT)
        return Response(status=HTTPStatus.BAD_REQUEST)


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
    pagination_class = CustomPagination
    permission_classes = (IsAuthorAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        if self.request.user.is_authenticated:
            user = self.request.user
        else:
            user = None
        is_favorited = Recipe.objects.filter(
            is_fav__recipe=OuterRef('pk'),
            is_fav__user=user
        )
        is_in_shopping_cart = Recipe.objects.filter(
            is_in_shop_cart__recipe=OuterRef('pk'),
            is_in_shop_cart__user=user
        )
        return Recipe.objects.select_related('author').prefetch_related(
            'ingredients', 'tags'
        ).annotate(is_favorited=Exists(is_favorited),
                   is_in_shopping_cart=Exists(is_in_shopping_cart))

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeSerializer

    def add_recipe_in_favorite_or_shopping_list(self, serializer, pk, request):
        serializer = serializer(
            data={'user': request.user.pk,
                  'recipe': pk},
            context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=HTTPStatus.CREATED)

    @action(['POST'], detail=True, url_path='favorite',
            permission_classes=(permissions.IsAuthenticated,))
    def favorite(self, request, pk):
        return self.add_recipe_in_favorite_or_shopping_list(
            FavouriteCreateSerializer, pk, request
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        follow_obj = Favourite.objects.filter(user=request.user,
                                              recipe__pk=pk)
        if follow_obj.exists():
            follow_obj.delete()
            return Response(status=HTTPStatus.NO_CONTENT)
        return Response(status=HTTPStatus.BAD_REQUEST)

    @action(['POST'], detail=True, url_path='shopping_cart',
            permission_classes=(permissions.IsAuthenticated,))
    def shopping_cart(self, request, pk):
        return self.add_recipe_in_favorite_or_shopping_list(
            ShoppingListCreateSerializer, pk, request
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        follow_obj = ShoppingList.objects.filter(user=request.user,
                                                 recipe__pk=pk)
        if follow_obj.exists():
            follow_obj.delete()
            return Response(status=HTTPStatus.NO_CONTENT)
        return Response(status=HTTPStatus.BAD_REQUEST)

    def shopping_list(self, ingredients):
        shopping_list_for_txt = 'Список покупок:\n'
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            amount = ingredient['amount__sum']
            measurement_unit = ingredient['ingredient__measurement_unit']
            shopping_list_for_txt += f'{name} - {amount} {measurement_unit}\n'
        return shopping_list_for_txt

    @action(['GET'], detail=False, url_path='download_shopping_cart',
            permission_classes=(permissions.IsAuthenticated,))
    def download_shopping_cart(self, request):
        ingredients = IngredientInRecipe.objects.filter(
            recipe__is_in_shop_cart__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).order_by('ingredient__name').annotate(Sum('amount'))
        return FileResponse(self.shopping_list(ingredients), headers={
            'Content-Type': 'application/txt',
            'Content-Disposition': 'attachment; filename="shopping_cart.txt"',
        })
