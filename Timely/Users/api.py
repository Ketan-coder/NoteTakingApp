from django.http import JsonResponse
from rest_framework import generics, viewsets, status, filters
from rest_framework.permissions import AllowAny
from django.db import transaction
from rest_framework.authtoken.models import Token
from .serializers import RegisterSerializer
from django.contrib.auth.models import User
from .serializers import RegisterSerializer

from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from datetime import datetime
from .models import *
from .serializers import *
from rest_framework.exceptions import NotFound
from django.shortcuts import get_object_or_404

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