from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import *

router = DefaultRouter()
router.register(r'profile', ProfileViewSet, basename='profile')

urlpatterns = [
    path('api-register/', RegisterView.as_view(), name='api-register'),
    path('', include(router.urls)),
]
