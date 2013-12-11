from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.views.generic import TemplateView
from httpproxy.views import HttpProxy

from ufindit.views import RulesView

admin.autodiscover()

urlpatterns = patterns('',
    # Query difficulty URL
    url(r'(?P<task_id>[0-9]+)$',
        'querydifficulty.views.submit_query_difficulty',
        name='submit_query_difficulty'),
    url(r'(?P<task_id>[0-9]+)/u$',
        'querydifficulty.views.submit_url_problem', name='submit_url_problem'),
    url(r'(?P<game_id>[0-9]+)/survey$', 'querydifficulty.views.submit_survey_view',
        name='submit_survey_view'),

    # TODO: Ugly, but works
    url(r'^game/(?P<game_id>[0-9]+)/rules/1/$', RulesView.as_view(
        template_name='rules1.html'), name='rules1'),
    url(r'^game/(?P<game_id>[0-9]+)/rules/2/$', RulesView.as_view(
        template_name='rules2.html'), name='rules2'),
    url(r'^game/(?P<game_id>[0-9]+)/rules/3/$', RulesView.as_view(
        template_name='rules3.html'), name='rules3'),
    url(r'^game/(?P<game_id>[0-9]+)/rules/4/$', RulesView.as_view(
        template_name='rules4.html'), name='rules4'),
    url(r'^game/(?P<game_id>[0-9]+)/rules/5/$', RulesView.as_view(
        template_name='rules5.html'), name='rules5'),
    url(r'^game/(?P<game_id>[0-9]+)/rules/6/$', RulesView.as_view(
        template_name='rules6.html'), name='rules6'),

    # Analytics
    url(r'^qud/$', 'querydifficulty.views.query_url_problems_view',
        name='query_difficulty_admin'),
    url(r'^qud/(?P<game_id>[0-9]+)/$', 'querydifficulty.views.query_url_problems_view',
        name='query_difficulty_game_admin'),
)
