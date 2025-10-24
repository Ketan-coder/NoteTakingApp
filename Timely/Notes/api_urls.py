from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import *

router = DefaultRouter()
router.register(r'notebooks', NotebookViewSet, basename='notebook')
router.register(r'pages', PageViewSet, basename='page')
router.register(r'subpages', SubPageViewSet, basename='subpage')
router.register(r'remainders', RemainderViewSet, basename='remainder')
router.register(r'todos', TodoViewSet, basename='todo')
router.register(r'todogroup', TodoGroupViewSet, basename='todogroup')
router.register(r'sharednotebooks', SharedNotebookViewSet, basename='sharednotebook')

urlpatterns = [
    path('api-login/', CustomAuthToken.as_view(), name='api-login'),
    path('', include(router.urls)),
    # path('api/notebooks/', NotebookAPIView.as_view(), name='notebooks-list'),
    # path('api/notebooks/<int:pk>/', NotebookAPIView.as_view(), name='notebooks-detail'),
]
