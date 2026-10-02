from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AuthorViewSet, GenreViewSet

app_name = 'library'

router = DefaultRouter()
router.register('authors', AuthorViewSet, basename='author')
router.register('genres', GenreViewSet, basename='genre')

urlpatterns = [
    path('', include(router.urls)),
]
