from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.views.generic import TemplateView
from httpproxy.views import HttpProxy

admin.autodiscover()

urlpatterns = patterns('',
    # Query difficulty URL
    url(r'(?P<task_id>[0-9]+)$',
        'querydifficulty.views.submit_query_difficulty',
        name='submit_query_difficulty'),
    url(r'(?P<game_id>[0-9]+)/survey$', 'querydifficulty.views.submit_survey_view',
        name='submit_survey_view'),
)
