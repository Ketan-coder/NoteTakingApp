from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from .models import Notebook
from .serializers import NotebookSerializer
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from Users.models import Profile

# @method_decorator(csrf_exempt, name='dispatch')
# class NotebookViewSet(viewsets.ViewSet):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]

#     """
#     API endpoint for managing notebooks.
#     """
    
#     def list(self, request):
#         notebooks = Notebook.objects.filter(user=request.user)
#         serializer = NotebookSerializer(notebooks, many=True)
#         return Response(serializer.data)

#     def create(self, request):
#         serializer = NotebookSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save(user=request.user)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def retrieve(self, request, pk=None):
#         try:
#             notebook = Notebook.objects.get(pk=pk, user=request.user)
#         except Notebook.DoesNotExist:
#             return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

#         serializer = NotebookSerializer(notebook)
#         return Response(serializer.data)

#     def update(self, request, pk=None):
#         try:
#             notebook = Notebook.objects.get(pk=pk, user=request.user)
#         except Notebook.DoesNotExist:
#             return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

#         serializer = NotebookSerializer(notebook, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def destroy(self, request, pk=None):
#         try:
#             notebook = Notebook.objects.get(pk=pk, user=request.user)
#         except Notebook.DoesNotExist:
#             return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

#         notebook.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)

# Working
class NotebookViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing notebooks.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = NotebookSerializer

    def get_queryset(self):
        """
        Retrieve all notebooks belonging to the authenticated user.
        """
        user = self.request.user
        profile = Profile.objects.filter(user=user).first()
        if not profile:
            return Notebook.objects.none()
        return Notebook.objects.filter(author=profile)

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
        return Response({'token': token.key, 'user_id': user.id, 'username': user.username})