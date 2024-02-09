from django_filters import FilterSet, ModelMultipleChoiceFilter, NumberFilter

from recipes.models import Recipe, Tag


class RecipeFilter(FilterSet):
    tags = ModelMultipleChoiceFilter(queryset=Tag.objects.all(),
                                     field_name='tags__slug',
                                     to_field_name='slug',)
    is_favorited = NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = NumberFilter(method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('author',)

    def filter_is_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(is_fav__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(is_in_shop_cart__user=self.request.user)
        return queryset
