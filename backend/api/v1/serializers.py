import base64
from django.core.files.base import ContentFile
from rest_framework.serializers import (
    Serializer,
    ModelSerializer,
    SerializerMethodField,
    ImageField,
    CharField,
    ValidationError,
)

from users.models import User


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
            # Пароль не будет возвращаться в ответах
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        # Создаем пользователя с хешированным паролем
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            avatar=validated_data.get('avatar'),
        )
        return user

    # def get_image_url(self, obj):
    #     if obj.avatar:
    #         return obj.avatar.url
    #     else:
    #         return None

    def get_is_subscribed(self, obj):
        # request = self.context.get('request')
        # return bool(
        #     request
        #     and request.user.is_authenticated
        #     and request.user.follower.filter(following=obj).exists()
        # )
        return False


class SetPasswordSerializer(Serializer):
    new_password = CharField(required=True, write_only=True)
    current_password = CharField(required=True, write_only=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise ValidationError("Текущий пароль неверный")
        return value

    def update(self, instance, validated_data):
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance
