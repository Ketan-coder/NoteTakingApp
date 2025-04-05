from django.urls import path
from .api import RegisterView

urlpatterns = [
    path('api-register/', RegisterView.as_view(), name='api-register'),
]
