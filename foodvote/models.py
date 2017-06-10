from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Group(models.Model):
	name = models.TextField()
	end_date = models.DateTimeField()
	create_date = models.DateTimeField(default=timezone.now)
	hash_field = models.TextField()
	create_by = models.ForeignKey(User, on_delete=models.CASCADE)
	location = models.TextField(default='seattle')
	
class User_Group(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	group = models.ForeignKey(Group, on_delete=models.CASCADE)

class Restaurant(models.Model):
	name = models.TextField()
	address = models.TextField()
	rating = models.IntegerField(default=0)
	rating_img = models.TextField()
	location = models.TextField()
	img = models.TextField(default='')
	url = models.TextField()
	hash_field = models.TextField()


class Restaurant_Group(models.Model):
	restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
	group = models.ForeignKey(Group, on_delete=models.CASCADE)
	hash_field = models.TextField()
	keep = models.BooleanField(default=False)

class Vote(models.Model):
	restaurant_group = models.ForeignKey(Restaurant_Group, on_delete=models.CASCADE)
	user_group = models.ForeignKey(User_Group, on_delete=models.CASCADE)
	upvote = models.BooleanField(default=False)
	downvote = models.BooleanField(default=False)




# Create your models here.
