import re

from rest_framework import serializers

from users.serializers import UserSerializer

from .models import Author, Book, Genre, Loan


class AuthorSerializer(serializers.ModelSerializer):
    """Сериализатор автора."""

    full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Author
        fields = (
            "id",
            "first_name",
            "last_name",
            "full_name",
            "biography",
            "birth_date",
        )

    def get_full_name(self, obj):
        return f"{obj.last_name} {obj.first_name}"


class GenreSerializer(serializers.ModelSerializer):
    """Сериализатор жанра."""

    class Meta:
        model = Genre
        fields = ("id", "name", "description")


# ============ КНИГИ ============


class BookReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения книги — с вложенными авторами и жанрами."""

    authors = AuthorSerializer(many=True, read_only=True)
    genres = GenreSerializer(many=True, read_only=True)
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model = Book
        fields = (
            "id",
            "title",
            "authors",
            "genres",
            "isbn",
            "publication_year",
            "publisher",
            "description",
            "total_copies",
            "available_copies",
            "is_available",
            "created_at",
            "updated_at",
        )


class BookWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления книги — принимает ID авторов и жанров."""

    class Meta:
        model = Book
        fields = (
            "id",
            "title",
            "authors",
            "genres",
            "isbn",
            "publication_year",
            "publisher",
            "description",
            "total_copies",
            "available_copies",
        )

    def validate_isbn(self, value):
        """Проверка формата ISBN (10 или 13 цифр, опционально с дефисами)."""
        if not value:
            return value
        # Убираем дефисы и пробелы для проверки
        cleaned = value.replace("-", "").replace(" ", "")
        if not re.fullmatch(r"\d{10}|\d{13}", cleaned):
            raise serializers.ValidationError(
                "ISBN должен содержать 10 или 13 цифр (можно с дефисами)."
            )
        return value

    def validate_publication_year(self, value):
        """Год издания не может быть в будущем."""
        if value is None:
            return value
        from django.utils import timezone

        current_year = timezone.now().year
        if value > current_year:
            raise serializers.ValidationError(f"Год издания не может быть больше {current_year}.")
        return value

    def validate(self, attrs):
        total = attrs.get("total_copies", getattr(self.instance, "total_copies", 1))
        available = attrs.get(
            "available_copies",
            getattr(self.instance, "available_copies", 1),
        )
        if available > total:
            raise serializers.ValidationError(
                {
                    "available_copies": (
                        "Доступных экземпляров не может быть " "больше общего количества."
                    ),
                }
            )
        return attrs


# ============ ВЫДАЧИ ============


class LoanReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения выдачи — с вложенными данными."""

    user = UserSerializer(read_only=True)
    book = BookReadSerializer(read_only=True)
    effective_status = serializers.CharField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Loan
        fields = (
            "id",
            "user",
            "book",
            "loan_date",
            "due_date",
            "return_date",
            "status",
            "effective_status",
            "is_overdue",
            "created_at",
            "updated_at",
        )


class LoanWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления выдачи — принимает ID."""

    class Meta:
        model = Loan
        fields = (
            "id",
            "user",
            "book",
            "due_date",
            "return_date",
            "status",
        )

    def validate_user(self, value):
        """Выдавать можно только читателям."""
        if value.role != "reader":
            raise serializers.ValidationError("Выдача книги возможна только читателю.")
        return value

    def validate(self, attrs):
        """Проверки при создании выдачи."""
        # При обновлении не проверяем
        if self.instance is not None:
            return attrs

        book = attrs.get("book")
        user = attrs.get("user")

        # Проверка: есть ли доступные экземпляры
        if book and book.available_copies < 1:
            raise serializers.ValidationError(
                {
                    "book": "Нет доступных экземпляров этой книги.",
                }
            )

        # Проверка: нет ли у читателя активной выдачи этой же книги
        if book and user:
            active_exists = Loan.objects.filter(
                user=user,
                book=book,
                status=Loan.STATUS_ISSUED,
            ).exists()
            if active_exists:
                raise serializers.ValidationError(
                    {
                        "book": "У этого читателя уже есть активная выдача данной книги.",
                    }
                )

        return attrs
