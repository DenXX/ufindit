
from urllib import unquote, urlencode

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect, HttpResponse, HttpRequest
from django.shortcuts import render, get_object_or_404
from django.views.generic.base import View

from ufindit.models import Player, PlayerTask, Serp, Game, PlayerGame
from ufindit.mturk import MTurkUser
from ufindit.search_proxy import SearchProxy
from ufindit.utils import get_query_terms

from query_url_problems.models import *

import settings

MTURK_JUDGEMENTS_PER_ASSIGNMENT = 2

class QueryUrlJudgementView(View):
    """ A view for judging query-url pairs """
    template_name = 'query_url_judging.html'
    mturk = False
    mturk_assignment = None

    def save_for_judgement(self, query_url_problem):
        obj = QueryUrlJudgement.objects.create(player=self.player, serp=query_url_problem.serp,
            task=query_url_problem.player_task.task, url=query_url_problem.url, judged=False)
        if self.mturk_assignment:
            self.mturk_assignment.judgements.add(obj)
            self.mturk_assignment.save()
        return obj

    def get_next_query_url(self, game_id):
        """ Currently extract next unjudged pair from querydifficulty tables """
        if QueryUrlJudgement.objects.filter(player=self.player, judged=False).exists():
            return QueryUrlJudgement.objects.filter(player=self.player, judged=False)[0]

        if self.mturk_assignment != None:
            if self.mturk_assignment.judgements.count() >= MTURK_JUDGEMENTS_PER_ASSIGNMENT:
                return None

        from querydifficulty.models import QueryUrlProblem
        qups = QueryUrlProblem.objects.exclude(url=None).filter(player_task__player_game__game__id=game_id)
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
        user = MTurkUser.get_mturk_user(workerId)
        login(request, user)
        return Player.objects.get(user=user)

    def init_mturk_assignment(self, assignmentId):
        """ Initialized mturk assignment """
        return QueryUrlJudgementAssignment.objects.create(player=self.player, mturk_assignment_id=assignmentId)

    def get_context(self, request):
        self.player = self.get_player(request)
        if self.mturk:
            if 'assignment_id' not in self.kwargs:
                if 'assignmentId' not in request.GET:
                    raise PermissionDenied
                self.mturk_assignment = self.init_mturk_assignment(request.GET['assignmentId'])
            else:
                self.mturk_assignment = QueryUrlJudgementAssignment.objects.get(id=self.kwargs['assignment_id'])

        judgement = self.get_next_query_url(self.kwargs['game_id'] if 'game_id' in self.kwargs else 1)
        games = Game.objects.all()
        if not judgement:
            return {'games': games, 'mturk': self.mturk}
        return {'judgement': judgement, 'query_terms': get_query_terms(judgement.serp.query),
            'result':judgement.serp.get_result_by_url(judgement.url.strip().replace('http/', 'http://').replace('https/', 'https://')),
            'games': games, 'mturk': self.mturk}

    def get(self, request, **kwargs):
        return self.get_response(request)

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
        return self.get_response(request)

    def get_response(self, request):
        try:
            context = self.get_context(request)
            if self.mturk and 'assignment_id' not in self.kwargs:
                return HttpResponseRedirect(
                    reverse('query_url_problems:query_url_judgement_mturk_assignment',
                        kwargs={'assignment_id':self.mturk_assignment.id}))

            if self.mturk and 'judgement' not in context:
                return HttpResponseRedirect(
                    reverse('query_url_problems:mturk_finish_assignment_view',
                        kwargs={'assignment_id':self.mturk_assignment.id}))
            return render(request, self.template_name, context)
        except Http404:
            return HttpResponseRedirect(reverse('login'))


def mturk_finish_assignment_view(request, assignment_id):
    assignment = QueryUrlJudgementAssignment.objects.get(id=assignment_id)
    # if assignment.judgements.count() < MTURK_JUDGEMENTS_PER_ASSIGNMENT:
    #     return HttpResponseRedirect(
    #         reverse('query_url_problems:query_url_judgement_mturk_assignment',
    #             kwargs={'assignment_id':assignment_id}))
    return HttpResponseRedirect(settings.MTURK_TASK_SUBMIT_URL +
        urlencode(dict(
            assignmentId=assignment.mturk_assignment_id,
            sb='submit HIT')))
