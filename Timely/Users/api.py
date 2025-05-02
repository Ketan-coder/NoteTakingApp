from django.http import JsonResponse
from rest_framework import generics, viewsets, status, filters
from rest_framework.permissions import AllowAny
from django.db import transaction
from rest_framework.authtoken.models import Token
from .serializers import RegisterSerializer
from django.contrib.auth.models import User
from .serializers import RegisterSerializer
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from datetime import datetime
from .models import *
from .serializers import *
from rest_framework.exceptions import NotFound
from django.shortcuts import get_object_or_404

class StandardResultsSetPagination(PageNumberPagination):
    """
    Custom pagination class for notebooks.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)

        return JsonResponse({
            "token": token.key,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
        }, status=status.HTTP_201_CREATED)

class ProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing users.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['firstName','lastName','email']  # Enables search via query parameter: ?search=<title>
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

        raise NotFound({"error": "User not found"})

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def get_queryset(self):
        """
        Optionally restricts the returned profiles to a given user,
        by filtering against a `username` query parameter in the URL.
        """
        queryset = Profile.objects.all()
        username = self.request.query_params.get('username', None)
        if username is not None:
            queryset = queryset.filter(user__username=username)
        return queryset


class UserPreferencesViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing user preferences.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = UserPreferencesSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['profile__firstName', 'profile__lastName', 'profile__email','profile__user__first_name', 'profile__user__last_name']  # Enables search via query parameter: ?search=<title>
    pagination_class = StandardResultsSetPagination
    lookup_field = 'id'  # Default lookup field

    def get_object(self):
        """
        Retrieve user preferences either by 'id'.
        """
        queryset = self.get_queryset()
        lookup_value = self.kwargs.get(self.lookup_field)

        if not lookup_value:
            raise NotFound({"error": "No lookup value provided"})

        # Try fetching by ID (integer)
        if str(lookup_value).isdigit():
            return get_object_or_404(queryset, id=int(lookup_value))

        raise NotFound({"error": "User preferences not found"})

    def get_queryset(self):
        """
        Retrieve the authenticated user's preferences.
        Optionally restricts the returned profiles to a given user,
        by filtering against a `username` query parameter in the URL.
        """
        user = self.request.user
        queryset = UserPreferences.objects.filter(profile__user=user)

        # Optional filtering by username if provided in query params
        username = self.request.query_params.get('username', None)
        if username:
            queryset = queryset.filter(profile__user__username=username)
        
        return queryset

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve user preferences based on the ID.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Create a new user preference for the authenticated user.
        """
        user = request.user
        profile = user.profile  # Assuming a profile is created for the user

        if not profile:
            return Response({"error": "User profile not found"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Save the preferences and associate with the user's profile
            serializer.save(profile=profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """
        Update an existing user preference. Only the user themselves can update.
        """
        instance = self.get_object()
        profile = request.user.profile

        if instance.profile != profile:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        """
        Partially update the user preferences (e.g., update only a few fields).
        """
        instance = self.get_object()
        profile = request.user.profile

        if instance.profile != profile:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """
        Delete an existing user preference. Only the user themselves can delete their preferences.
        """
        instance = self.get_object()
        profile = request.user.profile

        if instance.profile != profile:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        instance.delete()
        return Response({"message": "Preferences deleted successfully"}, status=status.HTTP_204_NO_CONTENT)