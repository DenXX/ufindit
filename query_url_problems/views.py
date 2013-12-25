from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponse, HttpRequest
from django.shortcuts import render, get_object_or_404
from django.views.generic.base import View

from ufindit.models import Player, PlayerTask, Serp, Game, PlayerGame
from ufindit.mturk import MTurkUser
from ufindit.search_proxy import SearchProxy
from ufindit.utils import get_query_terms

from query_url_problems.models import *

import settings

class QueryUrlJudgementView(View):
    """ A view for judging query-url pairs """
    template_name = 'query_url_judging.html'

    def save_for_judgement(self, query_url_problem):
        return QueryUrlJudgement.objects.create(player=self.player, serp=query_url_problem.serp,
            task=query_url_problem.player_task.task, url=query_url_problem.url, judged=False)

    def get_next_query_url(self):
        """ Currently extract next unjudged pair from querydifficulty tables """
        if QueryUrlJudgement.objects.filter(player=self.player, judged=False).exists():
            return QueryUrlJudgement.objects.filter(player=self.player, judged=False)[0]

        from querydifficulty.models import QueryUrlProblem
        qups = QueryUrlProblem.objects.exclude(url=None).filter(player_task__player_game__game__id=self.kwargs['game_id'])
        qups = qups.order_by('player_task__id', 'time')

        # TODO: Really ineffective, but don't know how to do better
        # Need the first currently unjudged result from 
        for qup in qups:
            if not QueryUrlJudgement.objects.filter(player=self.player, serp=qup.serp, url=qup.url).exists():
                return self.save_for_judgement(qup)


    def get_player(self, request):
        if request.user.is_authenticated():
            player, _ = Player.objects.get_or_create(user=request.user)
            return player
        if 'workerId' not in request.GET:
            raise Http404()
        workerId = request.GET['workerId']
        # hitId = request.GET['hitId']
        # assignmentId = request.GET['assignmentId']
        user = MTurkUser.get_mturk_user(workerId)
        login(request, user)
        return Player.objects.get(user=user)

    def get_context(self, request):
        self.player = self.get_player(request)
        judgement = self.get_next_query_url()
        games = Game.objects.all()
        if not judgement:
            return {'games': games}
        return {'judgement': judgement, 'query_terms': get_query_terms(judgement.serp.query),
            'result':judgement.serp.get_result_by_url(judgement.url.strip().replace('http/', 'http://').replace('https/', 'https://')),
            'games': games}

    def get(self, request, **kwargs):
        try:
            return render(request, self.template_name, self.get_context(request))
        except Http404:
            return HttpResponseRedirect(reverse('login'))

    def post(self, request, **kwargs):
        judgement = get_object_or_404(QueryUrlJudgement, id=request.POST['qujid'])
        if not judgement.judged:
            judgement.judged=True
            missing_terms = ''
            misinterpreted_terms = ''
            missing_relations = ''
            other_missing = ''
            other_problem = ''
            relevant = False
            if 'missing[]' in request.POST:
                missing_terms = ','.join(request.POST.getlist('missing[]'))
            if 'misinterpreted[]' in request.POST:
                misinterpreted_terms = ','.join(request.POST.getlist('misinterpreted[]'))
            if 'missing_relation[]' in request.POST:
                missing_relations = ','.join(request.POST.getlist('missing_relation[]'))
            if 'other_missing' in request.POST:
                other_missing = request.POST['other_missing']
            if 'other_problem' in request.POST:
                other_problem = request.POST['other_problem']
            if 'relevant' in request.POST:
                relevant = True
            judgement.relevant = relevant
            judgement.missing_terms = missing_terms
            judgement.misinterpreted_terms = misinterpreted_terms
            judgement.missing_relations = missing_relations
            judgement.other_missing = other_missing
            judgement.other_reason = other_problem
            judgement.save()

        try:
            return render(request, self.template_name, self.get_context(request))
        except Http404:
            return HttpResponseRedirect(reverse('login'))
