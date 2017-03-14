from django.shortcuts import render, redirect, get_object_or_404
from foodvote.forms import SearchForm, GroupForm 
from .models import User, Group, User_Group, Restaurant, Restaurant_Group, Vote
import io, json
from yelp.client import Client
from yelp.oauth1_authenticator import Oauth1Authenticator
from django.contrib.auth.decorators import login_required

# returns the homepage
@login_required(login_url='/login/')
def home(request):
	return render(request, 'foodvote/home.html')

# creates an instance of the given resturant and group (can be used later to elimante restaurant redundancy)
def create_restaurant_group(restaurant, group):
	restaurant_group = Restaurant_Group()
	restaurant_group.restaurant = restaurant
	restaurant_group.group = group
	restaurant_group.save()

# creares 10 restaurants for the given search term/location
def create_restaurant(searchterm, location, group, request):
	with io.open('foodvote/yelp_config_secret.json') as cred:
		creds = json.load(cred)
		auth = Oauth1Authenticator(**creds)
		client = Client(auth)

	params = {
		'term': searchterm,
		'limit': 10
	}
	
	response = client.search(location, **params)
	businesses = response.businesses
	for business in response.businesses:
		restaurant = Restaurant()
		restaurant.name = business.name
		restaurant.rating = business.rating
		restaurant.address = business.location.address[0]
		restaurant.rating_img = business.rating_img_url
		restaurant.location = business.location.display_address
		restaurant.img = business.image_url
		restaurant.url = business.url
		restaurant.save()
		create_restaurant_group(restaurant, group)
	return businesses

# makes a new group (renders form)
def create_group(request):
	if request.method == 'POST':
		form = SearchForm(request.POST)
		if form.is_valid():
			data = form.cleaned_data
			search = data['search']
			name = data['name']
			NewGroup = Group()
			NewGroup.name = data['name']
			NewGroup.end_date = data['date']
			NewGroup.search = data['search']	
			NewGroup.save()
			create_restaurant(search, data['location'], NewGroup, request)
			#need to figure out how to add users for each group
			#return group_page(NewGroup, request)
			return redirect('group_page', pk=NewGroup.pk)
			#every reload resends request and makes another group
	else:
		form=SearchForm()
	return render(request, 'foodvote/new_group.html', {'form': form})

# renders the list of restaurants in the group page
def group_page(request, pk):
	currentgroup = get_object_or_404(Group, pk=pk)
	# need to get user to check if user has voted on group then return appropriate page
	#votes = get_object_or_404(User_Group, group_id=pk, user_id=current_user)
	restaurant_groups = Restaurant_Group.objects.filter(group=currentgroup.id)
	restaurants = []
	for rg in restaurant_groups:
		restaurants.append(rg.restaurant)
	return render(request, 'foodvote/group.html', {'group': currentgroup, 'restaurants': restaurants})

# creates user
def create_user_group(group):
	user_group = User_Group()
	user_group.user = current #add current user
	user_group.group = group
	user_group.save()

# renders form then passes form text to 'group list'
def find_group(request):
	if request.method == 'POST':
		form = GroupForm(request.POST)
		if form.is_valid():
			data = form.cleaned_data
			groupval = data['group']
			print(groupval)
			return redirect('group_list', groupterm=groupval)
	else:
		form = GroupForm()
	return render(request, 'foodvote/find_group.html', {'form': form})

def group_list(request, groupterm):
	groups = Group.objects.filter(name=groupterm)
	return render(request, 'foodvote/group_list.html', {'groups': groups})



