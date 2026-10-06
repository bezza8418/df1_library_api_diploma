from rest_framework import status as http_status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from users.permissions import IsLibrarian, IsLibrarianOrReadOnly

from .filters import BookFilter
from .models import Author, Book, Genre, Loan
from .serializers import (
    AuthorSerializer,
    BookReadSerializer,
    BookWriteSerializer,
    GenreSerializer,
    LoanReadSerializer,
    LoanWriteSerializer,
)


class AuthorViewSet(viewsets.ModelViewSet):
    """CRUD для авторов. Читать — все авторизованные, изменять — только библиотекарь."""

    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = (IsLibrarianOrReadOnly,)

    filterset_fields = ("first_name", "last_name")
    search_fields = ("first_name", "last_name", "biography")
    ordering_fields = ("last_name", "first_name", "birth_date")
    ordering = ("last_name", "first_name")


class GenreViewSet(viewsets.ModelViewSet):
    """CRUD для жанров. Читать — все авторизованные, изменять — только библиотекарь."""

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsLibrarianOrReadOnly,)

    filterset_fields = ("name",)
    search_fields = ("name", "description")
    ordering_fields = ("name",)
    ordering = ("name",)


class BookViewSet(viewsets.ModelViewSet):
    """CRUD для книг. Читать — все авторизованные, изменять — только библиотекарь."""

    queryset = Book.objects.prefetch_related("authors", "genres").all()
    permission_classes = (IsLibrarianOrReadOnly,)
    filterset_class = BookFilter
    search_fields = (
        "title",
        "isbn",
        "publisher",
        "description",
        "authors__last_name",
        "authors__first_name",
    )
    ordering_fields = ("title", "publication_year", "created_at")
    ordering = ("title",)

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return BookReadSerializer
        return BookWriteSerializer


class LoanViewSet(viewsets.ModelViewSet):
    """
    CRUD для выдач.

    - Библиотекарь видит все выдачи, может создавать/менять.
    - Читатель видит только свои выдачи (read-only).
    """

    permission_classes = (IsLibrarianOrReadOnly,)
    filterset_fields = ("status", "book", "user")
    search_fields = ("book__title", "user__email")
    ordering_fields = ("loan_date", "due_date", "return_date")
    ordering = ("-loan_date", "-id")

    def get_queryset(self):
        """Читатель видит только свои выдачи, библиотекарь — все."""
        queryset = Loan.objects.select_related("user", "book").all()
        user = self.request.user
        if user.is_authenticated and user.is_reader:
            return queryset.filter(user=user)
        return queryset

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return LoanReadSerializer
        return LoanWriteSerializer

    def perform_create(self, serializer):
        """При создании выдачи уменьшаем available_copies у книги."""
        loan = serializer.save()
        book = loan.book
        book.available_copies = max(book.available_copies - 1, 0)
        book.save(update_fields=["available_copies", "updated_at"])

    @action(detail=True, methods=["post"], permission_classes=[IsLibrarian])
    def return_book(self, request, pk=None):
        """Вернуть книгу."""
        loan = self.get_object()
        try:
            loan.return_book()
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        serializer = LoanReadSerializer(loan)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsLibrarian])
    def mark_lost(self, request, pk=None):
        """Отметить книгу как потерянную."""
        loan = self.get_object()
        try:
            loan.mark_lost()
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        serializer = LoanReadSerializer(loan)
        return Response(serializer.data)
