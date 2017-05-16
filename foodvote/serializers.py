
from rest_framework import serializers
from .models import User, Group, User_Group, Restaurant, Restaurant_Group, Vote

class UserSerializer(serializers.ModelSerializer):
	class Meta:
		model = User
		fields = "__all__"

class GroupSerializer(serializers.ModelSerializer):
	class Meta:
		model = Group
		fields = "__all__"

class RestaurantSerializer(serializers.ModelSerializer):
	class Meta:
		model = Restaurant
		fields = "__all__"

class VoteSerializer(serializers.ModelSerializer):
	class Meta:
		model = Vote
		fields = "__all__"
