from ast import Sub
from rest_framework import serializers
from .models import *
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
    
class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'author', 'page_uuid','id']

    def create(self, validated_data):
        request = self.context.get('request')  # Get request from context
        profile = Profile.objects.get(user=request.user)  # Get profile of logged-in user
        validated_data['author'] = profile  # Assign logged-in user as author
        return super().create(validated_data)
    
class SubPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubPage
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'author', 'subpage_uuid','id']

    def create(self, validated_data):
        request = self.context.get('request')  # Get request from context
        profile = Profile.objects.get(user=request.user)  # Get profile of logged-in user
        validated_data['author'] = profile  # Assign logged-in user as author
        return super().create(validated_data)
    
class RemainderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Remainder
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'author', 'remainder_uuid','id']

    def create(self, validated_data):
        request = self.context.get('request')  # Get request from context
        profile = Profile.objects.get(user=request.user)  # Get profile of logged-in user
        validated_data['author'] = profile  # Assign logged-in user as author
        return super().create(validated_data)
    
class StickyNotesSerializer(serializers.ModelSerializer):
    class Meta:
        model = StickyNotes
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'author', 'stickynotes_uuid','id']

    def create(self, validated_data):
        request = self.context.get('request')  # Get request from context
        profile = Profile.objects.get(user=request.user)  # Get profile of logged-in user
        validated_data['author'] = profile  # Assign logged-in user as author
        return super().create(validated_data)
    
class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = '__all__'
        read_only_fields = '__all__'

    def create(self, validated_data):
        request = self.context.get('request')  # Get request from context
        profile = Profile.objects.get(user=request.user)  # Get profile of logged-in user
        validated_data['author'] = profile  # Assign logged-in user as author
        return super().create(validated_data)
    
class TodoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Todo
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'author', 'todo_uuid','id']

    def create(self, validated_data):
        request = self.context.get('request')  # Get request from context
        profile = Profile.objects.get(user=request.user)  # Get profile of logged-in user
        validated_data['author'] = profile  # Assign logged-in user as author
        return super().create(validated_data)
    
class SharedNotebookSerializer(serializers.ModelSerializer):
    class Meta:
        model = SharedNotebook
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'owner', 'sharednotebook_uuid','id']

    def create(self, validated_data):
        request = self.context.get('request')  # Get request from context
        profile = Profile.objects.get(user=request.user)  # Get profile of logged-in user
        validated_data['owner'] = profile  # Assign logged-in user as owner
        return super().create(validated_data)