from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import NotebookViewSet, CustomAuthToken, PageViewSet

router = DefaultRouter()
router.register(r'notebooks', NotebookViewSet, basename='notebook')
router.register(r'pages', PageViewSet, basename='page')

urlpatterns = [
    path('api-login/', CustomAuthToken.as_view(), name='api-login'),
    path('', include(router.urls)),
    # path('api/notebooks/', NotebookAPIView.as_view(), name='notebooks-list'),
    # path('api/notebooks/<int:pk>/', NotebookAPIView.as_view(), name='notebooks-detail'),
]
