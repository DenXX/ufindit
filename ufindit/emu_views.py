from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponse, HttpRequest
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from ufindit.logger import EventLogger
from ufindit.models import Game, Player, PlayerGame, PlayerTask

import settings

def emu_js(request, task_id):
    player_task = get_object_or_404(PlayerTask, id=task_id)
    context = {
        "event_logging_url": request.build_absolute_uri(reverse('emu_log_event', 
            kwargs={'task_id':task_id})),
        "save_page_url": request.build_absolute_uri(reverse('emu_save_page',
            kwargs={'task_id':task_id})),
        "proxy_url": request.build_absolute_uri(reverse('http_proxy',
            kwargs={'url':'','task_id':task_id})),
         }
    return render(request, 'emu_template.js', context,
        content_type="application/javascript")

def log_event(request, task_id):
    player_task = get_object_or_404(PlayerTask, id=task_id)
    EventLogger.emu_log_event(player_task, request.get_full_path())
    return HttpResponse("ok")


@csrf_exempt
def save_page(request, task_id):
    assert request.method == "POST"
    player_task = get_object_or_404(PlayerTask, id=task_id)
    EventLogger.emu_save_page(player_task, request.POST)
    return HttpResponse("ok")