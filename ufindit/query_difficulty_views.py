from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponse, HttpRequest
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from ufindit.logger import EventLogger
from ufindit.models import PlayerTask, QueryDifficulty, Serp

import settings

@csrf_exempt
def submit_query_difficulty(request, task_id):
    """
        This method accepts POST requests from query difficulty form and 
        saves answers to the database.
    """
    assert request.method == "POST"
    player_task = get_object_or_404(PlayerTask, id=task_id)
    serp = get_object_or_404(Serp, id=request.POST["serpid"])
    difficulty = ""
    if "query_difficulty" in request.POST:
        difficulty += request.POST["query_difficulty"]
    if len(request.POST["other_reason"]) > 0:
        difficulty += "\n" + request.POST["other_reason"]
    QueryDifficulty(player_task=player_task, serp=serp,
        difficulty=difficulty).save()
    return HttpResponse("ok")
