from django.shortcuts import render, redirect, get_object_or_404
from foodvote.forms import SearchForm, GroupForm 
from .models import User, Group, User_Group, Restaurant, Restaurant_Group, Vote
import io, json, os, hashlib
from yelp.client import Client
from yelp.oauth1_authenticator import Oauth1Authenticator
from django.contrib.auth.decorators import login_required
from ratelimit.decorators import ratelimit
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import UserSerializer, GroupSerializer, RestaurantSerializer, VoteSerializer
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from oauth2_provider.decorators import protected_resource

# returns the homepage
@ratelimit(key='ip', rate='5/m', block=True)
@login_required()
def home(request):
	return render(request, 'foodvote/home.html')


@ratelimit(key='ip', rate='5/m', block=True)
def app_login(request):
	error = None
	if request.method == 'POST':
		fields = request.POST
		usernameIn = fields.get("usernameInput")
		passwordIn = fields.get("passwordInput")
		user = authenticate(username=usernameIn, password=passwordIn)
		if user is not None:
			login(request, user)
			return redirect('home')
		else:
			print("auth unsuccessful")
			error = "Your username of password is incorrect"
	return render(request, 'registration/login.html', {'error' : error})

@ratelimit(key='ip', rate='5/m', block=True)
def app_registration(request):
	error = None
	if request.method == 'POST':
		fields = request.POST
		usernameIn = fields.get("usernameInput")
		passwordIn = fields.get("passwordInput")
		passwordIn2 = fields.get("passwordInput2")
		emailIn = fields.get("emailInput")
		qs = User.objects.all()
		u = qs.filter(username = usernameIn).exists()
		u2 = qs.filter(email = emailIn).exists()
		if u or u2:
			error = "Username or email has already been used"
		else:
			if passwordIn == passwordIn2:
				user = User.objects.create_user(usernameIn, emailIn)
				user.set_password(passwordIn)
				user.save()
				return redirect('login')
			else:
				error = "Passwords do not match"
		
	return render(request, 'registration/registration.html', {'error' : error})


@ratelimit(key='ip', rate='5/m', block=True)
@login_required()
def my_list(request):
	me = request.user.id
	groups = Group.objects.all().filter(create_by=me)
	return render(request, 'foodvote/group_list.html', {'groups': groups})


# creates an instance of the given resturant and group (can be used later to elimante restaurant redudcreate_restaurant_group(restaurant, group):
def create_restaurant_group(restaurant, group, hashtext):
	restaurant_group = Restaurant_Group()
	restaurant_group.restaurant = restaurant
	restaurant_group.group = group
	restaurant_group.hashfield = hashtext
	restaurant_group.keep = False
	restaurant_group.save()
	return restaurant_group

# creares 10 restaurants for the given search term/location
def create_restaurant(searchterm, location, group, request):
	with io.open('static/yelp_config_secret.json') as cred:
		creds = json.load(cred)
		auth = Oauth1Authenticator(**creds)
		client = Client(auth)

	params = {
		'term': searchterm,
		'limit': 5
	}
	
	response = client.search(location, **params)
	businesses = []
	randomhash = os.urandom(4).encode('hex')	
	for business in response.businesses:
		prehash = business.name + business.location.address[0]
		hashstring = hashlib.md5(prehash.encode()).hexdigest()
		restaurant = None
		if Restaurant.objects.all().filter(hash_field=hashstring).exists():
			savedrests = Restaurant.objects.get(hash_field=hashstring)
			restaurant = savedrests
		else:
			restaurant = Restaurant()
			restaurant.name = business.name
			restaurant.rating = business.rating
			restaurant.address = business.location.address[0]
			restaurant.rating_img = business.rating_img_url
			restaurant.location = business.location.display_address
			restaurant.img = business.image_url
			restaurant.url = business.url
			restaurant.hash_field = hashstring
			restaurant.save()
		businesses.append(create_restaurant_group(restaurant, group, randomhash))
	return businesses

# makes a new group (renders form)
@ratelimit(key='ip', rate='5/m', block=True)
@login_required()
def create_group(request):
	if request.method == 'POST':
		form = SearchForm(request.POST)
		if form.is_valid():
			data = form.cleaned_data
			search = data['search']
			name = data['name']
			current_user = request.user.id
			NewGroup = Group()
			NewGroup.name = data['name']
			NewGroup.end_date = data['date']
			NewGroup.search = data['search']
			NewGroup.create_by_id = current_user
			NewGroup.save()
			businesses = create_restaurant(search, data['location'], NewGroup, request)
			return render(request, 'foodvote/addrest.html', {'rg': businesses, 'group': NewGroup})
	else:
		form=SearchForm()
	return render(request, 'foodvote/new_group.html', {'form': form})

# renders the list of restaurants in the group page
@ratelimit(key='ip', rate='5/m', block=True)
@login_required()
def group_page(request, pk):
	currentgroup = get_object_or_404(Group, pk=pk)
	currentuser = request.user.id
	usergroup = User_Group.objects.all().filter(group=currentgroup, user=currentuser)
	message = None
	if request.method == 'POST':
		votes = request.POST.getlist('vote')
		if usergroup.exists():
			pastvotes = Vote.objects.all().filter(user_group=usergroup)
			for vote in pastvotes:
				vote.delete()	
			usergroup = User_Group.objects.get(group=currentgroup, user=currentuser)
		else: 
			usergroup = create_user_group(currentgroup, request)
		for vote in votes:
			newVote = Vote()
			newVote.user_group = usergroup
			rest_group = get_object_or_404(Restaurant_Group, pk=vote)
			newVote.restaurant_group = rest_group
			newVote.upvote = True
			newVote.save()
		return redirect('result', pk=pk)
	# need to get user to check if user has voted on group then return appropriate page
	else:
		if usergroup.exists():
			message = "You have already voted. Voting again will erase previous votes"	
		restaurant_groups = Restaurant_Group.objects.filter(group=currentgroup.id)
		restaurants = []
		for rg in restaurant_groups:
			restaurants.append(rg.restaurant)
	return render(request, 'foodvote/group.html', {'group': currentgroup,'rg': restaurant_groups, 'message': message})


@ratelimit(key='ip', rate='5/m', block=True)
@login_required()
def add_rest(request, pk):
	if request.method == 'POST':
		fields = request.POST
		searchterm = fields.get("search")
		groupterm = fields.get("group")
		print(groupterm)
		group = Group.objects.get(pk=groupterm)
		
		location = group.location
		businesses = create_restaurant(searchterm, location, group, request)
		return render(request, 'foodvote/addrest.html', {'rg': businesses, 'group': group})
	else:
		group = Group.objects.get(pk=pk)
		return render(request, 'foodvote/addsearch.html', {'group': group})

@ratelimit(key='ip', rate='5/m', block=True)
@login_required()
def add_chose(request):
	if request.method == 'POST':
		votes = request.POST.getlist('vote')
		group_key = request.POST.get('key')
		for vote in votes:
			rest_group = Restaurant_Group.objects.get(pk=vote)
			rest_group.keep = True
			rest_group.save()
		group = Group.objects.get(pk=group_key)
		rgroup_list = Restaurant_Group.objects.filter(group_id=group.id)
		for rgroup in rgroup_list:
			if rgroup.keep is False:
				rgroup.delete()
	return redirect('group_page', pk=group_key)
	

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
@login_required()
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
@login_required()
def group_list(request, groupterm):
	groups = Group.objects.filter(name=groupterm)
	return render(request, 'foodvote/group_list.html', {'groups': groups})

@ratelimit(key='ip', rate='5/m', block=True)
@login_required()
def get_results(request, pk):
	group = get_object_or_404(Group, pk=pk)
	rgs = Restaurant_Group.objects.filter(group=pk)
	leading = []
	leadCount = 0
	for rg in rgs:
		votes = Vote.objects.filter(restaurant_group=rg, upvote=True)
		if(votes.count() == leadCount):
			leading.append(rg)	
		elif(votes.count() > leadCount):
			leadCount = votes.count()
			leading = []
			leading.append(rg)
	return render(request, 'foodvote/result.html', {'rg': leading, 'count': leadCount, 'group': group})


@ratelimit(key='ip', rate='10/m', block=True)
@protected_resource()
@api_view(['GET', 'POST'])
def api_group(request, format=None):
	if request.method == 'GET':
		groups = Group.objects.all()
		serializer = GroupSerializer(groups, many=True)
		return Response(serializer.data)
	elif request.method == 'POST':
		serializer = GroupSerializer(data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@ratelimit(key='ip', rate='10/m', block=True)
@protected_resource()
@api_view(['GET', 'POST'])
def api_restaurant(request, format=None):
	if request.method == 'GET':
		rests = Restaurant.objects.all()
		serializer = RestaurantSerializer(rests, many=True)
		return Response(serializer.data)
	elif request.method == 'POST':
		serializer = RestaurantSerializer(data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@ratelimit(key='ip', rate='10/m', block=True)
@protected_resource()
@api_view(['GET', 'POST'])
def api_vote(request, pk, format=None):
	if request.method == 'GET':
		users = Vote.objects.get(user_group=pk)
		serializer = VoteSerializer(users, many=True)
		return Response(serializer.data)
	elif request.method == 'POST':
		serializer = VoteSerializer(data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@ratelimit(key='ip', rate='10/m', block=True)
@protected_resource()
@api_view(['GET', 'POST'])
def api_user(request, format=None):
	if request.method == 'GET':
		users = User.objects.all()
		serializer = UserSerializer(users, many=True)
		return Response(serializer.data)
	elif request.method == 'POST':
		serializer = UserSerializer(data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	

