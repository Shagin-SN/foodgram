from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)
    list_per_page = 50
    ordering = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1
    verbose_name = 'Ингредиент'
    verbose_name_plural = 'Ингредиенты рецепта'
    autocomplete_fields = ('ingredient',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'author', 'cooking_time',
        'pub_date', 'ingredients_count', 'tags_list',
        'favorites_count'
    )
    list_display_links = ('id', 'name')
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('tags', 'cooking_time', 'pub_date')
    readonly_fields = ('pub_date', 'favorites_count_display')
    filter_horizontal = ('tags',)
    inlines = (RecipeIngredientInline,)
    list_per_page = 30
    date_hierarchy = 'pub_date'

    fieldsets = (
        ('Основная информация', {
            'fields': ('author', 'name', 'image', 'text')
        }),
        ('Детали рецепта', {
            'fields': ('cooking_time', 'tags')
        }),
        ('Статистика', {
            'fields': ('pub_date', 'favorites_count_display'),
            'classes': ('collapse',)
        }),
    )

    def ingredients_count(self, obj):
        return obj.recipe_ingredients.count()
    ingredients_count.short_description = 'Кол-во ингредиентов'

    def tags_list(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])
    tags_list.short_description = 'Теги'

    def favorites_count(self, obj):
        return obj.favorites.count()
    favorites_count.short_description = 'В избранном'

    def favorites_count_display(self, obj):
        return obj.favorites.count()
    favorites_count_display.short_description = ('Количество добавлений'
                                                 ' в избранное')


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount', 'measurement_unit')
    list_display_links = ('id', 'recipe')
    search_fields = ('recipe__name', 'ingredient__name')
    list_filter = ('ingredient__measurement_unit',)
    list_per_page = 50
    autocomplete_fields = ('recipe', 'ingredient')

    def measurement_unit(self, obj):
        return obj.ingredient.measurement_unit
    measurement_unit.short_description = 'Единица измерения'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'recipes_count')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'slug')
    list_per_page = 30
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)

    def recipes_count(self, obj):
        return obj.recipes.count()
    recipes_count.short_description = 'Кол-во рецептов'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_display_links = ('id', 'user')
    search_fields = ('user__username', 'user__email', 'recipe__name')
    list_per_page = 50


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_display_links = ('id', 'user')
    search_fields = ('user__username', 'user__email', 'recipe__name')
    list_per_page = 50


admin.site.site_header = 'Администрирование Foodgram'
admin.site.site_title = 'Foodgram Admin'
admin.site.index_title = 'Панель управления Foodgram'
