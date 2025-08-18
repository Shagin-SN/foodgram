from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

from users.models import User
from .serializers import UserSerializer, SetPasswordSerializer


class UserViewSet(viewsets.ModelViewSet):
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
            serializer = self.get_serializer(
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
        serializer_class=SetPasswordSerializer,
    )
    def set_password(self, request):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'status': 'password set'},
                        status=status.HTTP_204_NO_CONTENT)
