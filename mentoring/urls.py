from django.conf.urls import patterns, include, url
import views
import surveys.views
import matches.views

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', views.home),

    # surveys
    url(r'^surveys/mentor/?$', surveys.views.survey, {"survey_id": 1}, name='surveys-mentor'),
    url(r'^surveys/mentee/?$', surveys.views.survey, {"survey_id": 2}, name='surveys-mentee'),
    url(r'^surveys/done/?$', surveys.views.done, name='surveys-done'),

    # matches
    url(r'^matches/match/?$', matches.views.match, name='matches-match'),

    # auth
    url(r'^accounts/login/$', 'django_cas.views.login', name='accounts-login'),
    url(r'^accounts/logout/$', 'django_cas.views.logout', name='accounts-logout', kwargs={"next_page": "/"}),
    # Examples:
    # url(r'^$', 'example.views.home', name='home'),
    # url(r'^example/', include('example.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
