from urllib import unquote, urlencode
import urllib2

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponse, HttpRequest
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from ufindit.logger import EventLogger
from ufindit.models import Player, PlayerTask, Serp, Game, PlayerGame
from querydifficulty.models import QueryUrlProblem, QueryDifficulty, Survey

import settings

@csrf_exempt
def submit_query_difficulty(request, task_id):
    """
        This method accepts POST requests from query difficulty form and 
        saves answers to the database.
    """
    assert request.method == "POST"
    assert "openTimer" in request.POST
    player_task = get_object_or_404(PlayerTask, id=task_id)
    serp = get_object_or_404(Serp, id=request.POST["serpid"])
    time = request.POST["openTimer"]
    difficulty = ""
    if "query_difficulty" in request.POST:
        difficulty += "\n".join(request.POST.getlist("query_difficulty"))
    if len(request.POST["other_reason"]) > 0:
        difficulty += "\n" + request.POST["other_reason"]
    QueryDifficulty(player_task=player_task, serp=serp, panelDwellTime=int(time),
        difficulty=difficulty).save()
    return HttpResponse("ok")


@csrf_exempt
def submit_url_problem(request, task_id):
    """
        This method accepts POST requests from query url problem form and 
        saves answers to the database.
    """
    assert request.method == "POST"
    player_task = get_object_or_404(PlayerTask, id=task_id)
    serp = get_object_or_404(Serp, id=request.POST["serpid"])
    rank = int(request.POST['rank'])-1 # Because page uses 1-based ranks
    missing_terms = ''
    misinterpreted_terms = ''
    missing_relation_terms = ''
    extra = ''
    if 'missing[]' in request.POST:
        missing_terms = ','.join(request.POST.getlist('missing[]'))
    if 'misinterpreted[]' in request.POST:
        misinterpreted_terms = ','.join(request.POST.getlist('misinterpreted[]'))
    if 'missing_relation[]' in request.POST:
        missing_relation_terms = ','.join(request.POST.getlist('missing_relation[]'))
    if 'extra' in request.POST:
        extra = request.POST['extra']
    QueryUrlProblem(player_task=player_task, serp=serp, doc_rank=rank,
        url=request.POST['rank'], missing_terms=missing_terms,
        misinterpreted_terms=misinterpreted_terms, missing_relations=missing_relation_terms,
        extra=extra).save()
    return HttpResponse("ok")

@login_required
def submit_survey_view(request, game_id):
    if request.method != 'POST':
        raise Http404()

    game = get_object_or_404(Game, id=game_id, active=True)
    fields = ['like', 'again', 'easy', 'distract', 'query_easy']
    for field in fields:
        if field not in request.POST:
            return render(request, 'survey.html', {'game':game, 'errors': True})

    player = get_object_or_404(Player, user=request.user)
    player_game = get_object_or_404(PlayerGame, player=player, game=game)
    if not player_game.finish:
        raise Http404()

    survey = Survey(player_game=player_game, liked=request.POST['like'],
        repeat=request.POST['again'], difficult=request.POST['easy'],
        distracting=request.POST['distract'], qdiffEasy=request.POST['query_easy'],
        qdiffComment=request.POST['qdiff_feedback'] if 'qdiff_feedback' in \
            request.POST else '',
        comments=request.POST['feedback'] if 'feedback' in request.POST else '')
    survey.save()
    
    message = ""
    if player_game.assignmentId:
        return HttpResponseRedirect(settings.MTURK_TASK_SUBMIT_URL +
            urlencode(dict(
                assignmentId=player_game.assignmentId,
                sb='submit HIT')))
 
    return render(request, 'game_over.html', {'game':game, "message":message})
