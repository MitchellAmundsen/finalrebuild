from django.conf.urls import url
from . import views

urlpatterns = [
	url(r'^$', views.home, name='home'),
	url(r'^create$', views.create_group, name='create'),
	url(r'^group_page/(?P<pk>\d+)/$', views.group_page, name='group_page'),
	url(r'^find$', views.find_group, name='find'),
	url(r'^group_list/(?P<groupterm>\S+)/$', views.group_list, name='group_list'),
	url(r'^result/(?P<pk>\d+)/$', views.get_results, name='result'),
	url(r'^api/group/$', views.api_group, name="api_group"),
	url(r'^api/restaurant/$', views.api_restaurant, name="api_restaurant"),
	url(r'^api/vote/(<?P<pk>\d+)/$', views.api_vote, name="api_vote"),
	url(r'^api/user/$', views.api_user, name="api_user"),
	
]	



