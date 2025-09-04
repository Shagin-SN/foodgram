import base64

from django.core.files.base import ContentFile
from django.db import transaction
from rest_framework.serializers import (CurrentUserDefault, HiddenField,
                                        ImageField, ModelSerializer,
                                        PrimaryKeyRelatedField, ReadOnlyField,
                                        SerializerMethodField, ValidationError)

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Follow, User


class Base64ImageField(ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class UserSerializer(ModelSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
            'password',
        )
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and request.user.follower.filter(following=obj).exists()
        )


class UserAvatarSerializer(ModelSerializer):
    avatar = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = User
        fields = ('avatar',)


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientReadSerializer(ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientReadSerializer(ModelSerializer):
    id = ReadOnlyField(source='ingredient.id')
    name = ReadOnlyField(source='ingredient.name')
    measurement_unit = ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientWriteSerializer(ModelSerializer):
    id = PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeReadSerializer(ModelSerializer):

    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = RecipeIngredientReadSerializer(
        many=True, source='recipe_ingredients'
    )
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        read_only_fields = fields

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and Favorite.objects.filter(user=request.user, recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and ShoppingCart.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        )


class RecipeWriteSerializer(ModelSerializer):

    tags = PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, required=True
    )
    ingredients = RecipeIngredientWriteSerializer(
        many=True, source='recipe_ingredients', required=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def validate(self, data):
        tags = data.get('tags', [])
        ingredients = data.get('recipe_ingredients', [])

        if not tags:
            raise ValidationError(
                {'tags': 'Добавьте хотя бы один тег.'}
            )
        if len({tag.id for tag in tags}) != len(tags):
            raise ValidationError(
                {'tags': 'Теги должны быть уникальными.'}
            )

        if not ingredients:
            raise ValidationError(
                {'ingredients': 'Добавьте хотя бы один ингредиент.'}
            )
        if len({item['ingredient'].id for item in ingredients}) != len(
            ingredients
        ):
            raise ValidationError(
                {'ingredients': 'Ингредиенты должны быть уникальными.'}
            )

        return data

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('recipe_ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self._create_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('recipe_ingredients', [])
        tags = validated_data.pop('tags', [])

        instance = super().update(instance, validated_data)
        instance.tags.set(tags)
        instance.recipe_ingredients.all().delete()
        self._create_ingredients(instance, ingredients)
        return instance

    @staticmethod
    def _create_ingredients(recipe, ingredients):
        objs = [
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=item['ingredient'].id,
                amount=item['amount'],
            )
            for item in ingredients
        ]
        RecipeIngredient.objects.bulk_create(objs)


class ShortRecipeSerializer(ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(UserSerializer):
    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = (
            UserSerializer.Meta.fields
            + ('is_subscribed', 'recipes', 'recipes_count')
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and Follow.objects.filter(
                user=request.user,
                following=obj
            ).exists()
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get(
            'recipes_limit')
        recipes = obj.recipes.all()

        if recipes_limit and recipes_limit.isdigit():
            recipes = recipes[:int(recipes_limit)]

        return ShortRecipeSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class FollowSerializer(ModelSerializer):
    user = HiddenField(default=CurrentUserDefault())
    following = PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Follow
        fields = ('user', 'following')

    def validate(self, data):
        user = data['user']
        following = data['following']

        if user == following:
            raise ValidationError(
                'Нельзя подписаться на самого себя'
            )

        if Follow.objects.filter(user=user, following=following).exists():
            raise ValidationError(
                'Вы уже подписаны на этого пользователя'
            )

        return data

    def to_representation(self, instance):
        return SubscriptionSerializer(
            instance.following,
            context=self.context
        ).data


class FavoriteSerializer(ModelSerializer):
    user = HiddenField(default=CurrentUserDefault())
    recipe = PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']

        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError(
                'Рецепт уже в избранном'
            )

        return data

    def to_representation(self, instance):
        return ShortRecipeSerializer(
            instance.recipe,
            context=self.context
        ).data


class ShoppingCartSerializer(ModelSerializer):
    user = HiddenField(default=CurrentUserDefault())
    recipe = PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']

        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError(
                'Рецепт уже в списке покупок'
            )

        return data

    def to_representation(self, instance):
        return ShortRecipeSerializer(
            instance.recipe,
            context=self.context
        ).data
