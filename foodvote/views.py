from django.shortcuts import render, redirect, get_object_or_404
from foodvote.forms import SearchForm, GroupForm 
from .models import User, Group, User_Group, Restaurant, Restaurant_Group, Vote
import io, json
from yelp.client import Client
from yelp.oauth1_authenticator import Oauth1Authenticator
from django.contrib.auth.decorators import login_required
from ratelimit.decorators import ratelimit

# returns the homepage
@ratelimit(key='ip', rate='5/m', block=True)
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
		'limit': 5
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
@ratelimit(key='ip', rate='5/m', block=True)
@login_required(login_url='/login/')
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
@ratelimit(key='ip', rate='5/m', block=True)
@login_required(login_url='/login/')
def group_page(request, pk):
	currentgroup = get_object_or_404(Group, pk=pk)
	if request.method == 'POST':
		votes = request.POST.getlist('vote')
		current_user_group = create_user_group(currentgroup, request)
		for vote in votes:
			newVote = Vote()
			newVote.user_group = current_user_group

			rest_group = get_object_or_404(Restaurant_Group, pk=vote)
			newVote.restaurant_group = rest_group
			newVote.upvote = True
			newVote.save()
		return redirect('result', pk=pk)
	# need to get user to check if user has voted on group then return appropriate page
	else:
		restaurant_groups = Restaurant_Group.objects.filter(group=currentgroup.id)
		restaurants = []
		for rg in restaurant_groups:
			restaurants.append(rg.restaurant)
	return render(request, 'foodvote/group.html', {'group': currentgroup,'rg': restaurant_groups})

# creates user
def create_user_group(groupinput, request):
	user_group = User_Group()

	user = request.user._wrapped if hasattr(request.user, '_wrapped') else request.user
	user_group.user = user #add current user

	user_group.group = groupinput
	user_group.save()
	return user_group

# renders form then passes form text to 'group list'
@ratelimit(key='ip', rate='5/m', block=True)
@login_required(login_url='/login/')
def find_group(request):
	if request.method == 'POST':
		form = GroupForm(request.POST)
		if form.is_valid():
			data = form.cleaned_data
			groupval = data['group']
			return redirect('group_list', groupterm=groupval)
	else:
		form = GroupForm()
	return render(request, 'foodvote/find_group.html', {'form': form})


@ratelimit(key='ip', rate='5/m', block=True)
@login_required(login_url='/login/')
def group_list(request, groupterm):
	groups = Group.objects.filter(name=groupterm)
	return render(request, 'foodvote/group_list.html', {'groups': groups})

@ratelimit(key='ip', rate='5/m', block=True)
@login_required(login_url='/login/')
def get_results(request, pk):
	group = get_object_or_404(Group, pk=pk)
	rgs = Restaurant_Group.objects.filter(group=pk)
	leading = 'none'
	leadCount = 0
	for rg in rgs:
		votes = Vote.objects.filter(restaurant_group=rg, upvote=True)
		if(votes.count() > leadCount):
			leadCount = votes.count()
			leading = rg
	return render(request, 'foodvote/result.html', {'rg': leading, 'count': leadCount})


