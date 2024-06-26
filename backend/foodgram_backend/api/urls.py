from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (IngredientViewSet, FoodgramUserViewSet, RecipeViewSet,
                    TagViewSet)

router = DefaultRouter()
router.register(r'users', FoodgramUserViewSet, basename='user')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'ingredients', IngredientViewSet, basename='ingredient')
router.register(r'recipes', RecipeViewSet, basename='recipe')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken'))
]
