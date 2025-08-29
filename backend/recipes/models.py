import base64

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import (CASCADE, CharField, DateTimeField, ForeignKey,
                              ImageField, ManyToManyField, Model,
                              PositiveSmallIntegerField, SlugField, TextField,
                              UniqueConstraint)
from users.models import User

from .constants import (INGREDIENT_MAX_LENGTH, MEASUREMENT_UNIT_MAX_LENGTH,
                        MIN_AMOUNT, MAX_AMOUNT, MIN_COOKING_TIME, MAX_COOKING_TIME,
                        TAG_MAX_LENGTH, MAX_RECIPE_NAME_LENGTH)


class Tag(Model):
    name = CharField(
        'Название тега',
        max_length=TAG_MAX_LENGTH,
        unique=True
    )
    slug = SlugField(
        'Идентификатор тега',
        max_length=TAG_MAX_LENGTH,
        unique=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(Model):
    name = CharField(
        'Название ингредиента',
        max_length=INGREDIENT_MAX_LENGTH
    )
    measurement_unit = CharField(
        'Единица измерения',
        max_length=MEASUREMENT_UNIT_MAX_LENGTH
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(Model):
    author = ForeignKey(
        User,
        on_delete=CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта'
    )
    name = CharField(
        'Название рецепта',
        max_length=MAX_RECIPE_NAME_LENGTH
    )
    image = ImageField(
        'Изображение рецепта',
        upload_to='recipes/images/'
    )
    text = TextField(
        'Описание рецепта'
    )
    ingredients = ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты'
    )
    tags = ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги'
    )
    cooking_time = PositiveSmallIntegerField(
        'Время приготовления (минуты)',
        validators=(MinValueValidator(MIN_COOKING_TIME,
                                      f'Время готовки не может быть меньше'
                                      f' {MIN_COOKING_TIME} мин.'),
                    MaxValueValidator(MAX_COOKING_TIME,
                                      f'Время готовки не может быть больше'
                                      f' {MAX_COOKING_TIME} мин.'),)
    )
    pub_date = DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )
    short_hash = CharField(
        max_length=10,
        unique=True,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def generate_short_hash(self):
        id_bytes = str(self.pk).encode()
        short_hash = base64.urlsafe_b64encode(id_bytes).decode('utf-8')
        return short_hash.rstrip('=')

    def get_short_link(self, request=None):
        if not self.short_hash:
            return None
        if request is not None:
            domain = request.build_absolute_uri('/')[:-1]
            return f'{domain}/s/{self.short_hash}'

    def save(self, *args, **kwargs):
        if not self.short_hash and self.pk:
            self.short_hash = self.generate_short_hash()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class RecipeIngredient(Model):
    recipe = ForeignKey(
        Recipe,
        on_delete=CASCADE,
        related_name='recipe_ingredients'
    )
    ingredient = ForeignKey(
        Ingredient,
        on_delete=CASCADE,
        related_name='ingredient_recipes'
    )
    amount = PositiveSmallIntegerField(
        'Количество',
        validators=(MinValueValidator(MIN_AMOUNT,
                                      f'Время готовки не может быть меньше'
                                      f' {MIN_AMOUNT}'),
                    MaxValueValidator(MAX_AMOUNT,
                                      f'Время готовки не может быть больше'
                                      f' {MAX_AMOUNT}'),)
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return (f'{self.ingredient.name} {self.amount} '
                f'{self.ingredient.measurement_unit}')


class Favorite(Model):
    user = ForeignKey(
        User,
        on_delete=CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = ForeignKey(
        'Recipe',
        on_delete=CASCADE,
        related_name='favorited_by',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил в избранное {self.recipe}'


class ShoppingCart(Model):
    user = ForeignKey(
        User,
        on_delete=CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь'
    )
    recipe = ForeignKey(
        'Recipe',
        on_delete=CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил в список покупок {self.recipe}'
