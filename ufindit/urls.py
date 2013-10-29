from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.views.generic import TemplateView
from httpproxy.views import HttpProxy

from ufindit.views import GameView

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'ufindit.views.index', name='index'),
    url(r'^game/(?P<game_id>[0-9]+)/$', GameView.as_view(), name='game'),
    url(r'^game/(?P<game_id>[0-9]+)/over$', GameView.as_view(is_game_over=True),
        name='game_over'),

    url(r'^(?P<task_id>[0-9]+)/s$', 'ufindit.views.search', 
        {'template':settings.SERP_TEMPLATE_NAME}, name='search'),

    # Login/Logout/Registration URL
    url(r'^login$', 'django.contrib.auth.views.login',
        {'template_name': 'login.html'}, name='login'),
    url(r'^logout$', 'django.contrib.auth.views.logout_then_login',
        name='logout'),
    url(r'^registration$', 'ufindit.views.register', name='register'),

    # Password reset urls
    url(r'^reset/done$', 'django.contrib.auth.views.password_reset_done',
        {'template_name': 'reset_done.html'}, name='password_reset_done'),
    url(r'^reset/$', 'django.contrib.auth.views.password_reset',
        {'template_name': 'reset.html'}, name='password_reset'),
    url(r'^reset/(?P<uidb36>[a-zA-Z0-9]+)/(?P<token>.+)/$',
        'django.contrib.auth.views.password_reset_confirm',
        {'template_name': 'reset_confirm.html'}, name='password_reset_confirm'),
    url(r'^reset/complete$', 'django.contrib.auth.views.password_reset_complete',
        {'template_name': 'reset_complete.html'}, name='password_reset_complete'),

    # Proxy
    url(r'^(?P<task_id>[0-9]*)/http/(?P<url>.*)$', HttpProxy.as_view(
        view_name='http_proxy', mode='playrecord',
        user_agent=settings.PROXY_USER_AGENT), name='http_proxy'),
    # Serp links
    url(r'^http/(?P<task_id>[0-9]*)/(?P<serp_id>[0-9]*)/(?P<url>.*)$', 
        'ufindit.views.http_proxy_decorator', name='http_proxy_decorator'),

    # EMU and event logging
    url(r'^(?P<task_id>[0-9]*)/emu/emu.js$', 'ufindit.emu_views.emu_js',
        name='emu_js'),
    url(r'^(?P<task_id>[0-9]*)/emu/log$', 'ufindit.emu_views.log_event',
        name='emu_log_event'),
    url(r'^(?P<task_id>[0-9]*)/emu/save_page$', 'ufindit.emu_views.save_page',
        name='emu_save_page'),

    # MTurk related urls
    url(r'^(?P<game_id>[0-9]*)/mturk_publish/(?P<sandbox>[01])$', 
        'ufindit.mturk.publish_game_view', name='mturk_publish_game'),
    url(r'^mturk_demo$', TemplateView.as_view(template_name='mturk_demo.html'),
        name='mturk_demo'),
    url(r'^mturk_demo_search$', TemplateView.as_view(
        template_name='mturk_demo_search.html'), name='mturk_demo_search'),

    # Query difficulty URLs
    (r'^qdiff/', include('querydifficulty.urls', app_name='querydifficulty',
        namespace='querydifficulty')),

    # Admin views
    url(r'^admin/', include(admin.site.urls)),
) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
