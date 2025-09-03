from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import F, Q
from django.db.models.constraints import CheckConstraint, UniqueConstraint

from .constants import MAX_NAMES_LENGTH


class FoodgramUser(AbstractUser):
    """Модель пользователя с аватаром"""

    email = models.EmailField(
        'Email',
        unique=True,
    )
    avatar = models.ImageField(
        upload_to='users/',
        null=True,
        default=None
    )

    first_name = models.CharField(
        'first_name',
        max_length=MAX_NAMES_LENGTH,
    )

    last_name = models.CharField(
        'last_name',
        max_length=MAX_NAMES_LENGTH,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name',)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return (
            f'Пользователь {self.username} '
            f'Email: {self.email}'
        )


User = get_user_model()


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='follower',
        verbose_name='Подписчик',
    )
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='follows',
        verbose_name='Подписка',
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=('user', 'following'), name='unique_follow'
            ),
            CheckConstraint(
                check=~Q(user=F('following')), name='not_follow_self'
            ),
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
