from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import NotebookViewSet, CustomAuthToken

router = DefaultRouter()
router.register(r'notebooks', NotebookViewSet, basename='notebook')

urlpatterns = [
    path('api-login/', CustomAuthToken.as_view(), name='api-login'),
    path('', include(router.urls)),
    # path('api/notebooks/', NotebookAPIView.as_view(), name='notebooks-list'),
    # path('api/notebooks/<int:pk>/', NotebookAPIView.as_view(), name='notebooks-detail'),
]
