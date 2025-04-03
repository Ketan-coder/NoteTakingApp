from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Profile
        fields = ['id', 'user', 'bio', 'email_confirmation_token']
        read_only_fields = ['email_confirmation_token']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user, created = User.objects.get_or_create(**user_data)
        profile = Profile.objects.create(user=user, **validated_data)
        return profile
