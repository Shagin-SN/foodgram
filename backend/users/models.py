from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

MAX_NAME_LENGTH = 150


class FoodgramUser(AbstractUser):
    """Модель пользователя с аватаром"""

    username = models.CharField(
        max_length=MAX_NAME_LENGTH,
        unique=True,
        validators=[UnicodeUsernameValidator(),],
    )
    email = models.EmailField(
        "Email",
        unique=True,
    )
    avatar = models.ImageField(
        upload_to='users/',
        null=True,
        default=None
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return (
            f"Пользователь {self.username} "
            f"Email: {self.email}"
        )


User = get_user_model()
