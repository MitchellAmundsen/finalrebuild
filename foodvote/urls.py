from django.conf.urls import url
from . import views

urlpatterns = [
	url(r'^$', views.home, name='home'),
	url(r'^create$', views.create_group, name='create'),
	url(r'^group_page/(?P<pk>\d+)/$', views.group_page, name='group_page'),
	url(r'^find$', views.find_group, name='find'),
	url(r'^group_list/(?P<groupterm>\S+)/$', views.group_list, name='group_list'),
]



