from rest_framework import serializers
from .models import Notebook
from Users.models import Profile
class NotebookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notebook
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'author', 'notebook_uuid','id']

    def create(self, validated_data):
        request = self.context.get('request')  # Get request from context
        profile = Profile.objects.get(user=request.user)  # Get profile of logged-in user
        validated_data['author'] = profile  # Assign logged-in user as author
        return super().create(validated_data)