from rest_framework import permissions


class IsLibrarian(permissions.BasePermission):
    """Доступ только для библиотекарей (и суперпользователей)."""

    message = 'Действие доступно только библиотекарю.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_librarian or request.user.is_superuser)
        )


class IsReader(permissions.BasePermission):
    """Доступ только для читателей."""

    message = 'Действие доступно только читателю.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_reader
        )


class IsLibrarianOrReadOnly(permissions.BasePermission):
    """
    Библиотекарь может всё.
    Читатель — только безопасные методы (GET, HEAD, OPTIONS).
    """

    message = 'Изменение доступно только библиотекарю.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        return bool(request.user.is_librarian or request.user.is_superuser)


class IsOwnerOrLibrarian(permissions.BasePermission):
    """
    Объект доступен владельцу (например, свою выдачу читатель видит)
    или библиотекарю / суперпользователю.
    """

    message = 'Доступ только к своим объектам или для библиотекаря.'

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_librarian or request.user.is_superuser:
            return True

        # Предполагаем, что у объекта есть поле user
        return getattr(obj, 'user', None) == request.user
