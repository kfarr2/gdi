from django.conf.urls import patterns, include, url
import views
import surveys.views

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', views.home),
    url(r'^surveys/mentor/?$', surveys.views.survey, {"survey_id": 1}, name='surveys-mentor'),
    url(r'^surveys/mentee/?$', surveys.views.survey, {"survey_id": 2}, name='surveys-mentee'),
    url(r'^surveys/done/?$', surveys.views.done, name='surveys-done'),
    # Examples:
    # url(r'^$', 'example.views.home', name='home'),
    # url(r'^example/', include('example.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
