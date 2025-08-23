from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (UserViewSet,
                    RecipeViewSet,
                    TagViewSet,
                    IngridientViewSet,
                    )

router_v1 = DefaultRouter()

router_v1.register(
    prefix='users',
    viewset=UserViewSet,
)
router_v1.register(
    prefix='recipes',
    viewset=RecipeViewSet,
)
router_v1.register(
    prefix='tags',
    viewset=TagViewSet,
)
router_v1.register(
    prefix='ingredients',
    viewset=IngridientViewSet,
)

urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
