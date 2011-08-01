from django.conf.urls.defaults import *
from .views import index

urlpatterns = patterns('',
   url(r'^emis/stats/$', index, name='stats'),
   url(r'^emis/stats/(?P<location_id>\d+)/$', index),
)
