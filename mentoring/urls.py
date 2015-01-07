from django.conf.urls import patterns, include, url
#import views
from mentoring import views as views
from mentoring.surveys import views as surveys
from mentoring.matches import views as matches
from mentoring.surveyadmin import views as surveyadmin

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', views.home),

    # surveys
    url(r'^surveys/mentor/?$', surveys.mentor, name='surveys-mentor'),
    url(r'^surveys/mentee/?$', surveys.mentee, name='surveys-mentee'),
    url(r'^surveys/done/?$', surveys.done, name='surveys-done'),
    url(r'^surveys/response/(\d+)/?$', surveys.response, name='surveys-response'),
    url(r'^surveys/report/(\d+)/?$', surveys.report, name='surveys-report'),

    # matches
    url(r'^matches/marry/?$', matches.marry, name='matches-marry'),
    url(r'^matches/divorce/?$', matches.divorce, name='matches-divorce'),
    url(r'^matches/engage/?$', matches.engage, name='matches-engage'),
    url(r'^matches/breakup/?$', matches.breakup, name='matches-breakup'),
    url(r'^matches/complete/?$', matches.complete, name='matches-complete'),
    url(r'^matches/report/?$', matches.report, name='matches-report'),
    # mentors and mentee administration
    url(r'^(mentors)/delete/?$', matches.remove, name='mentors-delete'),
    url(r'^(mentees)/delete/?$', matches.remove, name='mentees-delete'),

    # management
    url(r'^manage/?$', matches.manage, name='manage'),
    url(r'^manage/match/?$', matches.match, name='manage-match'),
    url(r'^manage/ments/?$', matches.ments, name='manage-ments'),
    url(r'^manage/completions/?$', matches.completions, name='manage-completions'),
    url(r'^manage/settings/?$', matches.settings, name='manage-settings'),

    # admin
    url(r'^sadmin/?$', surveyadmin.admin, name='admin-surveys'),
    url(r'^sadmin/survey/(\d+)?$', surveyadmin.questions, name='admin-surveys-questions'),
    url(r'^sadmin/question/(\d+)?$', surveyadmin.question, name='admin-surveys-question'),


    # auth
    url(r'^accounts/login/$', 'djangocas.views.login', name='accounts-login'),
    url(r'^accounts/logout/$', 'djangocas.views.logout', name='accounts-logout', kwargs={"next_page": "/"}),
    # Examples:
    # url(r'^$', 'example.views.home', name='home'),
    # url(r'^example/', include('example.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
