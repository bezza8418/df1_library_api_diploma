from rest_framework import serializers

from .models import Author, Book, Genre


class AuthorSerializer(serializers.ModelSerializer):
    """Сериализатор автора."""

    full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Author
        fields = (
            'id',
            'first_name',
            'last_name',
            'full_name',
            'biography',
            'birth_date',
        )

    def get_full_name(self, obj):
        return f'{obj.last_name} {obj.first_name}'


class GenreSerializer(serializers.ModelSerializer):
    """Сериализатор жанра."""

    class Meta:
        model = Genre
        fields = ('id', 'name', 'description')


# ============ КНИГИ ============

class BookReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения книги — с вложенными авторами и жанрами."""

    authors = AuthorSerializer(many=True, read_only=True)
    genres = GenreSerializer(many=True, read_only=True)
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model = Book
        fields = (
            'id',
            'title',
            'authors',
            'genres',
            'isbn',
            'publication_year',
            'publisher',
            'description',
            'total_copies',
            'available_copies',
            'is_available',
            'created_at',
            'updated_at',
        )


class BookWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления книги — принимает ID авторов и жанров."""

    class Meta:
        model = Book
        fields = (
            'id',
            'title',
            'authors',
            'genres',
            'isbn',
            'publication_year',
            'publisher',
            'description',
            'total_copies',
            'available_copies',
        )

    def validate(self, attrs):
        total = attrs.get('total_copies', getattr(self.instance, 'total_copies', 1))
        available = attrs.get(
            'available_copies',
            getattr(self.instance, 'available_copies', 1),
        )
        if available > total:
            raise serializers.ValidationError({
                'available_copies': 'Доступных экземпляров не может быть больше общего количества.',
            })
        return attrs
