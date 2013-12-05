from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import user_passes_test
from django.views.generic import TemplateView

from analytics.views import GamesView, GameView

urlpatterns = patterns('',
    url(r'^games/$', user_passes_test(lambda u: u.is_staff)(GamesView.as_view()),
        name='games'),
    url(r'^games/(?P<game_id>[0-9]*)/$', user_passes_test(lambda u: u.is_staff)(GameView.as_view()),
        name='game_analytics'),
)
