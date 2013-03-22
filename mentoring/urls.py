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
    url(r'^surveys/mentor/?$', surveys.views.mentor, name='surveys-mentor'),
    url(r'^surveys/mentee/?$', surveys.views.mentee, name='surveys-mentee'),
    url(r'^surveys/done/?$', surveys.views.done, name='surveys-done'),
    url(r'^surveys/response/(\d+)/?$', surveys.views.response, name='surveys-response'),

    # matches
    url(r'^matches/marry/?$', matches.views.marry, name='matches-marry'),
    url(r'^matches/divorce/?$', matches.views.divorce, name='matches-divorce'),
    url(r'^matches/engage/?$', matches.views.engage, name='matches-engage'),
    url(r'^matches/breakup/?$', matches.views.breakup, name='matches-breakup'),
    url(r'^matches/complete/?$', matches.views.complete, name='matches-complete'),
    # mentors and mentee administration
    url(r'^(mentors)/delete/?$', matches.views.remove, name='mentors-delete'),
    url(r'^(mentees)/delete/?$', matches.views.remove, name='mentees-delete'),

    # management
    url(r'^manage/?$', matches.views.manage, name='manage'),
    url(r'^manage/match/?$', matches.views.match, name='manage-match'),
    url(r'^manage/ments?$', matches.views.ments, name='manage-ments'),

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
