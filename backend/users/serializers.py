from rest_framework.serializers import (
    ModelSerializer,
)

from users.models import User


class UserSerializer(ModelSerializer):
    """
    Сериализатор по пользователям
    """

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "bio",
            "role",
        )
