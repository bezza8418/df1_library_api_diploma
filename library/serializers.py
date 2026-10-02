from rest_framework import serializers

from .models import Author, Genre


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
