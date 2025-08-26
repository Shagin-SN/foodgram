from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from rest_framework import filters, status
from rest_framework.decorators import action, api_view
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import (GenericViewSet, ModelViewSet,
                                     ReadOnlyModelViewSet)

from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomLimitOffsetPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (FollowSerializer, IngredientReadSerializer,
                          RecipeReadSerializer, RecipeWriteSerializer,
                          SetPasswordSerializer, ShortRecipeSerializer,
                          SubscriptionSerializer, TagSerializer,
                          UserAvatarSerializer, UserCreateSerializer,
                          UserSerializer)
from users.models import Follow, User


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    pagination_class = LimitOffsetPagination
    lookup_field = 'id'
    search_fields = ('username',)
    filter_backends = [filters.SearchFilter]
    http_method_names = ('get', 'post', 'patch', 'delete', 'put')
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ['patch', 'delete']:
            self.permission_classes = (IsAuthenticated,)
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    @action(
        detail=False,
        methods=['get', 'patch'],
        permission_classes=(IsAuthenticated,),
    )
    def me(self, request: Request) -> Response:
        user = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        elif request.method == 'PATCH':
            serializer = self.get_serializer(
                user,
                data=request.data,
                partial=True,
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,),
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = UserAvatarSerializer(
                user,
                data={'avatar': request.data.get('avatar')},
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete()
                user.avatar = None
                user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['post'],
        url_path='set_password',
        permission_classes=(IsAuthenticated,),
    )
    def set_password(self, request):
        user = request.user
        serializer = SetPasswordSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'status': 'password set'},
                        status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        user = request.user
        following = User.objects.filter(follows__user=user)
        page = self.paginate_queryset(following)
        serializer = SubscriptionSerializer(page,
                                            many=True,
                                            context={'request': request},
                                            )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, id=None):
        user = request.user
        following = get_object_or_404(User, id=id)

        if user == following:
            return Response(
                {'detail': 'Нельзя подписаться на самого себя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.method == 'POST':
            if Follow.objects.filter(user=user, following=following).exists():
                return Response(
                    {'detail': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Follow.objects.create(user=user, following=following)

            serializer = SubscriptionSerializer(
                following,
                context={'request': request},
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            try:
                follow = Follow.objects.get(user=user, following=following)
            except Follow.DoesNotExist:
                return Response(
                    {'detail': 'Подписка не найдена'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class FollowViewSet(CreateModelMixin, ListModelMixin, GenericViewSet):
    serializer_class = FollowSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('following__username',)

    def get_queryset(self):
        return self.request.user.follower.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all().prefetch_related(
        'tags', 'recipe_ingredients__ingredient', 'author')
    pagination_class = CustomLimitOffsetPagination
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'get_short_link'):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link'
    )
    def get_short_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)

        if not recipe.short_hash:
            recipe.short_hash = recipe.generate_short_hash()
            recipe.save()

        return Response({
            "short-link": recipe.get_short_link(request=request)
        })

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'detail': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':

            if not Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'detail': 'Рецепт не найден'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.filter(user=user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'detail': 'Рецепт уже в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            if not ShoppingCart.objects.filter(
                user=user,
                recipe=recipe
            ).exists():
                return Response(
                    {'detail': 'Рецепт не найден'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.filter(user=user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(user=user)

        ingredients = {}
        for item in shopping_cart:
            for recipe_ingredient in item.recipe.recipe_ingredients.all():
                ingredient = recipe_ingredient.ingredient
                amount = recipe_ingredient.amount

                key = f"{ingredient.name} ({ingredient.measurement_unit})"
                if key in ingredients:
                    ingredients[key] += amount
                else:
                    ingredients[key] = amount

        shopping_list = "Список покупок:\n\n"
        for ingredient, amount in ingredients.items():
            shopping_list += f"{ingredient} - {amount}\n"

        response = Response(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; '
            'filename="shopping_list.txt"'
        )
        return response


@api_view(['GET'])
def redirect_short_link(request, short_hash):
    try:
        recipe = get_object_or_404(Recipe, short_hash=short_hash)
        return redirect('recipe-detail', pk=recipe.pk)

    except Recipe.DoesNotExist:
        return Response(
            {'detail': 'Страница не найдена.'},
            status=status.HTTP_404_NOT_FOUND
        )


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngridientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientReadSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,)
    filterset_class = IngredientFilter
