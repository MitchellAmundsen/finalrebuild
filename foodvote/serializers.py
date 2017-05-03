
from rest_framework import serializers
from .models import User, Group, User_Group, Restaurant, Restaurant_Group, Vote

class UserSerializer(serializers.Serializer):
	class Meta:
		model = User
		fields = "__all__"

class GroupSerializer(serializers.Serializer):
	class Meta:
		model = Group
		fields = "__all__"

class RestaurantSerializer(serializers.Serializer):
	class Meta:
		model = Restaurant
		fields = "__all__"

class VoteSerializer(serializers.Serializer):
	class Meta:
		model = Vote
		fields = "__all__"
