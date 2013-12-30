from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from httpproxy.views import HttpProxy

from ufindit.views import RulesView

from query_url_problems.views import QueryUrlJudgementView

admin.autodiscover()

urlpatterns = patterns('',
    # Judgememt
    url(r'judge/(?P<game_id>[0-9]+)/', QueryUrlJudgementView.as_view(),
        name='query_url_judgement'),

    # MTurk judgement URLs
    url(r'judge/mturk/start/$', QueryUrlJudgementView.as_view(mturk=True),
        name='query_url_judgement_mturk'),
    url(r'judge/mturk/(?P<assignment_id>[0-9]+)/$', QueryUrlJudgementView.as_view(mturk=True),
        name='query_url_judgement_mturk_assignment'),
    url(r'judge/mturk/(?P<assignment_id>[0-9]+)/done/$', 'query_url_problems.views.mturk_finish_assignment_view',
        name='mturk_finish_assignment_view'),
)
