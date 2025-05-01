from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from datetime import datetime
from Notes.utils import send_email
from .models import *
from .serializers import *
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from Users.models import Profile
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import NotFound
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.decorators import action

class StandardResultsSetPagination(PageNumberPagination):
    """
    Custom pagination class for notebooks.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class TodoResultsSetPagination(PageNumberPagination):
    """
    Custom pagination class for todos/reminders.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 200

# Working
class NotebookViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing notebooks.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = NotebookSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['title','body','is_public']  # Enables search via query parameter: ?search=<title>
    lookup_field = 'id'  # Default lookup field

    def get_object(self):
        """
        Retrieve a single notebook by either 'id' or 'uuid'.
        """
        queryset = self.get_queryset()
        lookup_value = self.kwargs.get(self.lookup_field)

        user = self.request.user
        profile = Profile.objects.filter(user=user).first()

        base_q = Notebook.objects.filter(Q(author=profile) | Q(shared_with=profile) | Q(is_public=True))

        if not lookup_value:
            raise NotFound({"error": "No lookup value provided"})

        # Try fetching by ID (integer)
        if str(lookup_value).isdigit():
            return get_object_or_404(base_q, id=int(lookup_value))

        # Try fetching by UUID
        try:
            return get_object_or_404(base_q, notebook_uuid=lookup_value)
        except ValueError:
            raise NotFound({"error": "Invalid UUID format"})

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_queryset(self):
        """
        Retrieve all notebooks belonging to the authenticated user.
        """
        user = self.request.user
        profile = Profile.objects.filter(user=user).first()
        if not profile:
            return Notebook.objects.none()
        # return Notebook.objects.filter(author=profile)
        queryset = Notebook.objects.filter(author=profile).order_by('priority')

        # Filtering via query parameters
        title = self.request.query_params.get('title')
        body = self.request.query_params.get('body')
        is_public = self.request.query_params.get('is_public')
        shared_with_me = self.request.query_params.get('shared_with_me')

        if body:
            queryset = queryset.filter(body__icontains=body)
        if title:
            queryset = queryset.filter(title__icontains=title)
        if is_public:
            queryset = Notebook.objects.filter(is_public=True)
        if shared_with_me and shared_with_me.lower() in ["true", "1"]:
            queryset = Notebook.objects.filter(shared_with=profile)

        return queryset

    def create(self, request, *args, **kwargs):
        """
        Create a new notebook and assign it to the authenticated user.
        """
        user = request.user
        profile = Profile.objects.filter(user=user).first()
        if not profile:
            return Response({"error": "User profile not found"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """
        Update an existing notebook. Only the owner can update it.
        """
        instance = self.get_object()
        profile = Profile.objects.get(user=request.user)

        if instance.author != profile:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        """
        Partially update a notebook (e.g., updating only the title).
        """
        instance = self.get_object()
        profile = Profile.objects.get(user=request.user)

        if instance.author != profile:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """
        Delete an existing notebook. Only the owner can delete it.
        """
        instance = self.get_object()
        profile = Profile.objects.get(user=request.user)

        if instance.author != profile:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        instance.delete()
        return Response({"message": "Notebook deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['get'], url_path='page-and-subpage-names')
    def get_page_and_subpage_names(self, request, id=None):
        """
        Custom endpoint to fetch only the names, id, and order of pages and subpages in a notebook.
        """
        notebook = self.get_object()

        # Pages of the notebook
        pages = Page.objects.filter(notebook=notebook).order_by('order')
        pages_data = PageNameSerializer(pages, many=True).data

        # Subpages nested under those pages
        subpages = SubPage.objects.filter(page__in=pages, notebook=notebook)
        subpages_data = SubPageNameSerializer(subpages, many=True).data

        return Response({
            "pages": pages_data,
            "subpages": subpages_data
        })
    
class PageViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing pages.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = PageSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['title','body','order']  # Enables search via query parameter: ?search=<title>
    lookup_field = 'id'  # Default lookup field

    def get_object(self):
        """
        Retrieve a single notebook by either 'id' or 'uuid'.
        """
        queryset = self.get_queryset()
        lookup_value = self.kwargs.get(self.lookup_field)

        if not lookup_value:
            raise NotFound({"error": "No lookup value provided"})

        # Try fetching by ID (integer)
        if str(lookup_value).isdigit():
            return get_object_or_404(queryset, id=int(lookup_value))

        # Try fetching by UUID
        try:
            return get_object_or_404(queryset, page_uuid=lookup_value)
        except ValueError:
            raise NotFound({"error": "Invalid UUID format"})

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_queryset(self):
        """
        Retrieve all pages belonging to the authenticated user.
        """
        user = self.request.user
        profile = Profile.objects.filter(user=user).first()
      
        if not profile:
            return Page.objects.none()
        # return Page.objects.filter(author=profile)
        
        accessible_notebooks = Notebook.objects.filter(Q(author=profile) | Q(shared_with=profile) | Q(is_public=True))
        queryset = Page.objects.filter(notebook__in=accessible_notebooks).order_by('order')

        # Filtering via query parameters
        title = self.request.query_params.get('title')
        body = self.request.query_params.get('body')
        if title:
            queryset = queryset.filter(title__icontains=title)
        if body:
            queryset = queryset.filter(body__icontains=body)

        return queryset

    def create(self, request, *args, **kwargs):
        """
        Create a new page and assign it to the authenticated user.
        """
        user = request.user
        profile = Profile.objects.filter(user=user).first()
        if not profile:
            return Response({"error": "User profile not found"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """
        Update an existing page. Only the owner can update it.
        """
        instance = self.get_object()
        profile = Profile.objects.get(user=request.user)

        if instance.author != profile:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        """
        Partially update a page (e.g., updating only the title).
        """
        instance = self.get_object()
        profile = Profile.objects.get(user=request.user)

        if instance.author != profile:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """
        Delete an existing page. Only the owner can delete it.
        """
        instance = self.get_object()
        profile = Profile.objects.get(user=request.user)

        if instance.author != profile:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        instance.delete()
        return Response({"message": "Page deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class SubPageViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing pages.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = SubPageSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['title','body']  # Enables search via query parameter: ?search=<title>
    lookup_field = 'id'  # Default lookup field

    def get_object(self):
        """
        Retrieve a single notebook by either 'id' or 'uuid'.
        """
        queryset = self.get_queryset()
        lookup_value = self.kwargs.get(self.lookup_field)

        if not lookup_value:
            raise NotFound({"error": "No lookup value provided"})

        # Try fetching by ID (integer)
        if str(lookup_value).isdigit():
            return get_object_or_404(queryset, id=int(lookup_value))

        # Try fetching by UUID
        try:
            return get_object_or_404(queryset, subpage_uuid=lookup_value)
        except ValueError:
            raise NotFound({"error": "Invalid UUID format"})

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_queryset(self):
        """
        Retrieve all pages belonging to the authenticated user.
        """
        user = self.request.user
        profile = Profile.objects.filter(user=user).first()
        if not profile:
            return SubPage.objects.none()
        # return SubPage.objects.filter(author=profile)
        # queryset = SubPage.objects.filter(author=profile).order_by('-created_at')

        accessible_notebooks = Notebook.objects.filter(Q(author=profile) | Q(shared_with=profile) | Q(is_public=True))
        queryset = SubPage.objects.filter(notebook__in=accessible_notebooks).order_by('-created_at')

        # Filtering via query parameters
        title = self.request.query_params.get('title')
        body = self.request.query_params.get('body')
        if title:
            queryset = queryset.filter(title__icontains=title)
        if body:
            queryset = queryset.filter(body__icontains=body)

        return queryset
    
    def create(self, request, *args, **kwargs):
        """
        Create a new subpage and assign it to the authenticated user.
        """
        user = request.user
        profile = Profile.objects.filter(user=user).first()
        if not profile:
            return Response({"error": "User profile not found"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """
        Update an existing subpage. Only the owner can update it.
        """
        instance = self.get_object()
        profile = Profile.objects.get(user=request.user)

        if instance.author != profile:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        """
        Partially update a subpage (e.g., updating only the title).
        """
        instance = self.get_object()
        profile = Profile.objects.get(user=request.user)

        if instance.author != profile:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """
        Delete an existing subpage. Only the owner can delete it.
        """
        instance = self.get_object()
        profile = Profile.objects.get(user=request.user)

        if instance.author != profile:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        instance.delete()
        return Response({"message": "Subpage deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class RemainderViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Reminders.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = RemainderSerializer
    pagination_class = TodoResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['title','body','is_favorite','is_completed','is_over']  # Enables search via query parameter: ?search=<title>
    lookup_field = 'id'  # Default lookup field

    def get_object(self):
        """
        Retrieve a single notebook by either 'id' or 'uuid'.
        """
        queryset = self.get_queryset()
        lookup_value = self.kwargs.get(self.lookup_field)

        if not lookup_value:
            raise NotFound({"error": "No lookup value provided"})

        # Try fetching by ID (integer)
        if str(lookup_value).isdigit():
            return get_object_or_404(queryset, id=int(lookup_value))

        # Try fetching by UUID
        try:
            return get_object_or_404(queryset, remainder_uuid=lookup_value)
        except ValueError:
            raise NotFound({"error": "Invalid UUID format"})

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_queryset(self):
        """
        Retrieve all reminders belonging to the authenticated user.
        """
        user = self.request.user
        profile = Profile.objects.filter(user=user).first()
        if not profile:
            return Remainder.objects.none()
        # return Remainder.objects.filter(author=profile)
        queryset = Remainder.objects.filter(author=profile).order_by('-created_at')

        # Filtering via query parameters
        title = self.request.query_params.get('title')
        body = self.request.query_params.get('body')
        is_favorite = self.request.query_params.get('is_favorite')
        is_completed = self.request.query_params.get('is_completed')
        is_over = self.request.query_params.get('is_over')
        if title:
            queryset = queryset.filter(title__icontains=title)
        if body:
            queryset = queryset.filter(body__icontains=body)
        if is_favorite:
            queryset = queryset.filter(is_favorite=is_favorite)
        if is_completed:
            queryset = queryset.filter(is_completed=is_completed)
        if is_over:
            queryset = queryset.filter(is_over=is_over)

        return queryset

    def create(self, request, *args, **kwargs):
        """
        Create a new reminder and assign it to the authenticated user.
        """
        user = request.user
        profile = Profile.objects.filter(user=user).first()
        if not profile:
            return Response({"error": "User profile not found"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """
        Update an existing reminder. Only the owner can update it.
        """
        instance = self.get_object()
        profile = Profile.objects.get(user=request.user)

        if instance.author != profile:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        """
        Partially update a reminder (e.g., updating only the title).
        """
        instance = self.get_object()
        profile = Profile.objects.get(user=request.user)

        if instance.author != profile:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """
        Delete an existing reminder. Only the owner can delete it.
        """
        instance = self.get_object()
        profile = Profile.objects.get(user=request.user)

        if instance.author != profile:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        instance.delete()
        return Response({"message": "Reminder deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class TodoViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing todos.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = TodoSerializer
    pagination_class = TodoResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['title','is_completed',]  # Enables search via query parameter: ?search=<title>
    lookup_field = 'id'  # Default lookup field

    def get_object(self):
        """
        Retrieve a single notebook by either 'id' or 'uuid'.
        """
        queryset = self.get_queryset()
        lookup_value = self.kwargs.get(self.lookup_field)

        if not lookup_value:
            raise NotFound({"error": "No lookup value provided"})

        # Try fetching by ID (integer)
        if str(lookup_value).isdigit():
            return get_object_or_404(queryset, id=int(lookup_value))

        # Try fetching by UUID
        try:
            return get_object_or_404(queryset, todo_uuid=lookup_value)
        except ValueError:
            raise NotFound({"error": "Invalid UUID format"})

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_queryset(self):
        """
        Retrieve all todos belonging to the authenticated user.
        """
        user = self.request.user
        profile = Profile.objects.filter(user=user).first()
        if not profile:
            return Todo.objects.none()
        # return Todo.objects.filter(author=profile)
        queryset = Todo.objects.filter(author=profile).order_by('-created_at')

        # Filtering via query parameters
        title = self.request.query_params.get('title')
        is_completed = self.request.query_params.get('is_completed')
        if title:
            queryset = queryset.filter(title__icontains=title)
        if is_completed:
            queryset = queryset.filter(is_completed=is_completed)
        
        return queryset

    def create(self, request, *args, **kwargs):
        """
        Create a new todo and assign it to the authenticated user.
        """
        user = request.user
        profile = Profile.objects.filter(user=user).first()
        if not profile:
            return Response({"error": "User profile not found"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """
        Update an existing todo. Only the owner can update it.
        """
        instance = self.get_object()
        profile = Profile.objects.get(user=request.user)

        if instance.author != profile:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        """
        Partially update a todo (e.g., updating only the title).
        """
        instance = self.get_object()
        profile = Profile.objects.get(user=request.user)

        if instance.author != profile:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """
        Delete an existing todo. Only the owner can delete it.
        """
        instance = self.get_object()
        profile = Profile.objects.get(user=request.user)

        if instance.author != profile:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        instance.delete()
        return Response({"message": "Todo deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class SharedNotebookViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing pages.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = SharedNotebookSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['notebook','sharedTo']  # Enables search via query parameter: ?search=<title>
    lookup_field = 'id'  # Default lookup field

    def get_object(self):
        """
        Retrieve a single notebook by either 'id' or 'uuid'.
        """
        queryset = self.get_queryset()
        lookup_value = self.kwargs.get(self.lookup_field)

        if not lookup_value:
            raise NotFound({"error": "No lookup value provided"})

        # Try fetching by ID (integer)
        if str(lookup_value).isdigit():
            return get_object_or_404(queryset, id=int(lookup_value))

        # Try fetching by UUID
        try:
            return get_object_or_404(queryset, sharednotebook_uuid=lookup_value)
        except ValueError:
            raise NotFound({"error": "Invalid UUID format"})

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_queryset(self):
        """
        Retrieve all shared notebooks belonging to the authenticated user.
        """
        user = self.request.user
        profile = Profile.objects.filter(user=user).first()
        if not profile:
            return SharedNotebook.objects.none()
        # return SharedNotebook.objects.filter(owner=profile)
        queryset = SharedNotebook.objects.filter(owner=profile).order_by('-shared_at')

        # Filtering via query parameters
        notebook = self.request.query_params.get('notebook')
        sharedTo = self.request.query_params.get('sharedTo')
        if notebook:
            queryset = queryset.filter(notebook=notebook)
        if sharedTo:
            queryset = queryset.filter(sharedTo=sharedTo)
        
        return queryset

    def create(self, request, *args, **kwargs):
        """
        Create a new shared notebook and assign it to the authenticated user.
        """
        user = request.user
        profile = Profile.objects.filter(user=user).first()
        if not profile:
            return Response({"error": "User profile not found"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """
        Update an existing shared notebook. Only the owner can update it.
        """
        instance = self.get_object()
        profile = Profile.objects.get(user=request.user)

        if instance.author != profile:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        """
        Partially update a shared notebook (e.g., updating only the title).
        """
        instance = self.get_object()
        profile = Profile.objects.get(user=request.user)

        if instance.author != profile:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """
        Delete an existing shared notebook. Only the owner can delete it.
        """
        instance = self.get_object()
        profile = Profile.objects.get(user=request.user)

        if instance.author != profile:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        instance.delete()
        return Response({"message": "Shared notebook deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

# Working Fine
class CustomAuthToken(ObtainAuthToken):
    """
    Custom authentication token for returning user_id and username with token.
    """
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        send_email(
                    to_email=user.email,
                    subject="Login Alert",
                    title="Login Alert Notification",
                    body=f"Your account with username '{user.username}' was accessed on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} via Mobile App. If this was not you, please reset your password to secure your account!.",
                    anchor_link="https://timely.pythonanywhere.com/accounts/password-reset/",
                    anchor_text="Reset Password",
                )
        return Response({'token': token.key, 'user_id': user.id, 'username': user.username, 'email': user.email, 'first_name': user.first_name, 'last_name': user.last_name}, status=status.HTTP_200_OK)