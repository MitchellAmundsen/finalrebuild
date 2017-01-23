from django import forms
from django.contrib.auth.models import User

class GroupForm(forms.Form):
	group = forms.CharField(label='Group Name', max_length=20)

class SearchForm(forms.Form):
	name = forms.CharField(label='Group Name', max_length=20)
	search = forms.CharField(label='Search Term', max_length=20)
	location = forms.CharField(label='Location', max_length=20)
	date = forms.DateTimeField(label='Meetup Time')



