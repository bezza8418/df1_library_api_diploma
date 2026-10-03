from rest_framework import viewsets

from users.permissions import IsLibrarianOrReadOnly

from .filters import BookFilter
from .models import Author, Book, Genre
from .serializers import (
    AuthorSerializer,
    BookReadSerializer,
    BookWriteSerializer,
    GenreSerializer,
)


class AuthorViewSet(viewsets.ModelViewSet):
    """CRUD для авторов. Читать — все авторизованные, изменять — только библиотекарь."""

    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = (IsLibrarianOrReadOnly,)

    # Фильтрация (точное совпадение)
    filterset_fields = ('first_name', 'last_name')

    # Поиск (частичное совпадение, регистронезависимый)
    search_fields = ('first_name', 'last_name', 'biography')

    # Сортировка
    ordering_fields = ('last_name', 'first_name', 'birth_date')
    ordering = ('last_name', 'first_name')  # по умолчанию


class GenreViewSet(viewsets.ModelViewSet):
    """CRUD для жанров. Читать — все авторизованные, изменять — только библиотекарь."""

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsLibrarianOrReadOnly,)

    filterset_fields = ('name',)
    search_fields = ('name', 'description')
    ordering_fields = ('name',)
    ordering = ('name',)


class BookViewSet(viewsets.ModelViewSet):
    """CRUD для книг. Читать — все авторизованные, изменять — только библиотекарь."""

    queryset = Book.objects.prefetch_related('authors', 'genres').all()
    permission_classes = (IsLibrarianOrReadOnly,)
    filterset_class = BookFilter  # ← изменили с filterset_fields на filterset_class
    search_fields = (
        'title',
        'isbn',
        'publisher',
        'description',
        'authors__last_name',
        'authors__first_name',
    )
    ordering_fields = ('title', 'publication_year', 'created_at')
    ordering = ('title',)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return BookReadSerializer
        return BookWriteSerializer
