from rest_framework import viewsets

from users.permissions import IsLibrarianOrReadOnly

from .models import Author, Genre
from .serializers import AuthorSerializer, GenreSerializer


class AuthorViewSet(viewsets.ModelViewSet):
    """CRUD для авторов. Читать — все авторизованные, изменять — только библиотекарь."""

    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = (IsLibrarianOrReadOnly,)


class GenreViewSet(viewsets.ModelViewSet):
    """CRUD для жанров. Читать — все авторизованные, изменять — только библиотекарь."""

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsLibrarianOrReadOnly,)
