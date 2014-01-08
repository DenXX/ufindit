from django.utils.timezone import now
from search_proxy import SearchProxy
from urllib import unquote, urlencode
import urllib2

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.template import RequestContext
from django.views.decorators.cache import cache_control
from django.views.generic.base import View


from httpproxy.views import HttpProxy
from ufindit.forms import RegistrationForm
from ufindit.logger import EventLogger
from ufindit.models import Game, Player, PlayerGame, PlayerTask, Serp, GameSurvey
from ufindit.mturk import MTurkUser
from ufindit.utils import get_query_terms

import settings

def index(request):
    context = RequestContext(request, 
        {'games' : Game.objects.filter(active = True)})
    return render(request, 'index.html', context)


def register(request):
    context = {}
    registration_form = RegistrationForm()
    if request.method == 'POST':
        registration_form = RegistrationForm(request.POST)
        if registration_form.is_valid():
            email = registration_form.cleaned_data['email']
            if User.objects.filter(email=email).exists():
                context['errors'] = 'User with this email already exists'
                context['registration_form'] = registration_form
                return render(request, 'registration.html', context)
            password = registration_form.cleaned_data['password']
            user = User.objects.create_user(email, email, password)
            user.save()
            user = authenticate(username=email, password=password)
            login(request, user)
            return HttpResponseRedirect(reverse('index'))
    context['registration_form'] = registration_form
    return render(request, 'registration.html', context)


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True, max_age=0)
def search(request, task_id, template='serp.html'):
    context = {'task_id':task_id}
    user = request.user
    player = Player.objects.get(user=request.user)
    player_task = get_object_or_404(PlayerTask, id=task_id)
    if 'q' in request.GET and request.GET['q'].strip() != '':
        query = unquote(request.GET['q']).decode('utf8')
        search_proxy = SearchProxy(settings.SEARCH_PROXY)
        context['query'] = query
        context['query_terms'] = get_query_terms(query)
        search_results = search_proxy.search(player, query)
        context['serpid'] = search_results.id
        # Log query event
        serp = get_object_or_404(Serp, id=search_results.id)
        paginator = Paginator(search_results, settings.RESULTS_PER_PAGE)
        page = request.GET.get('page')
        try:
            context['results'] = paginator.page(page)
            page = int(page)
        except PageNotAnInteger:
            context['results'] = paginator.page(1)
            page = 1
        except EmptyPage:
            context['results'] = paginator.page(paginator.num_pages)
            page = paginator.num_pages
        start_page = max([1, page - 3])
        end_page = min([paginator.num_pages + 1, page + 4])
        context['page_numbers'] = range(start_page, end_page)
        context['pages_number'] = paginator.num_pages
        # Log query event
        EventLogger.query(player_task, query, serp, context['results'].number)
    context['enable_emu'] = settings.ENABLE_EMU_LOGGING
    return render(request, template, context)


class GameView(View):
    '''
        Top level page for the game. The pages shows game top panel and 
        search box in a frame. It also accepts answers and skips with POST
        requests.
    '''
    is_game_over=False
    game_over_template = settings.GAME_OVER_TEMPLATE

    def check_user(self, request):
        if request.user.is_authenticated():
            return True
        if 'workerId' not in request.GET:
            return False
        workerId = request.GET['workerId']
        hitId = request.GET['hitId']
        assignmentId = request.GET['assignmentId']
        game = Game.objects.filter(hitId=hitId, active=True)
        if len(game) != 1:
            return False
        user = MTurkUser.get_mturk_user(workerId)
        login(request, user)
        return user.is_authenticated()

    def finish_game(self, request, player_game):
        if not player_game.finish:
            player_game.finish = now()
            player_game.save()

        if request.method == 'POST':
            fields = ['like', 'again', 'easy']
            for field in fields:
                if field not in request.POST:
                    return render(request, 'survey.html', {'errors': True})

            survey = GameSurvey(player_game=player_game, liked=request.POST['like'],
                repeat=request.POST['again'], difficult=request.POST['easy'],
                comments=request.POST['feedback'] if 'feedback' in request.POST else '')
            survey.save()
            
            return HttpResponseRedirect(reverse('game_over',
                kwargs={'game_id':player_game.game.id}))

        return render(request, 'survey.html', {})

     def game_over(self, request, player_game):
        context = {'message':'', 'game':player_game.game}
        if player_game.assignmentId:
            return HttpResponseRedirect(settings.MTURK_TASK_SUBMIT_URL +
                urlencode(dict(
                    assignmentId=player_game.assignmentId,
                    sb='submit HIT')))
        return render(request, self.game_over_template, context)


    def dispatch(self, request, **kwargs):
        # Check if the current request is a demo query from mturk
        if 'assignmentId' in request.GET and request.GET['assignmentId'] == \
            'ASSIGNMENT_ID_NOT_AVAILABLE':
            return HttpResponseRedirect(reverse('mturk_demo'))

        if not self.check_user(request):
            raise Http404()
        game = get_object_or_404(Game, id=kwargs['game_id'], active=True)
        player, _ = Player.objects.get_or_create(user=request.user)
        player_game, created = PlayerGame.objects.get_or_create(player=player,
            game=game)

        # Save assignment ID if just created
        if created and ('assignmentId' in request.GET):
            player_game.assignmentId = request.GET['assignmentId']
            player_game.save()

        # If player opens the game, then he accepted the rules
        if not player_game.rules_accepted:
            if 'accepted' in request.GET:
                player_game.rules_accepted = True
            else:
                return HttpResponseRedirect(reverse('rules', kwargs={'game_id':kwargs['game_id']}))

        player_game.save()
        if self.is_game_over:
            if not player_game.finish:
                raise Http404()
            return self.game_over(request, player_game)

        if player_game.current_task_index >= \
            PlayerTask.objects.filter(player_game=player_game).count():
            return self.finish_game(request, player_game)

        current_task = get_object_or_404(PlayerTask, player_game=player_game,
            order=player_game.current_task_index)
        if current_task.start == None:
            current_task.start = now()
            current_task.save()
        # Check if the task wasn't finished
        assert current_task.finish == None
        
        # If form was submitted, either skipped or answered.
        if request.method == 'POST':
            return self.post(request, player_game, current_task)
        else:
            return self.get(request, game, current_task)


    def post(self, request, player_game, current_task):
        if request.POST.has_key('save_answer'):
            current_task.answer = request.POST['answer']
            current_task.answer_url = request.POST['answer_url']
            # Increment user score
            player_game.score += 1
            player_game.save()
        elif not request.POST.has_key('skip'):
            raise Http404
        # Save the current task
        player_game.current_task_index += 1
        player_game.save()
        current_task.finish = now()
        current_task.save()
        # Redirect back so that refresh doesn't cause form resend.
        return HttpResponseRedirect(reverse('game',
            kwargs={'game_id':player_game.game.id}))

    def get(self, request, game, current_task):
        context = { 'game' : game, 'player_task': current_task}
        return render(request, 'game.html', context)


def http_proxy_decorator(request, task_id, serp_id, url):
    player_task = get_object_or_404(PlayerTask, id=task_id)
    serp = get_object_or_404(Serp, id=serp_id)
    EventLogger.click(player_task, url, serp=serp)
    return HttpResponseRedirect(reverse('http_proxy', kwargs={'url':url,
        'task_id':task_id}))

class RulesView(View):
    """ Checks if user accepted rules and if not, shows  """
    
    template_name = 'rules.html'

    def get(self, request, game_id):
        game = get_object_or_404(Game, id=game_id, active=True)
        player, _ = Player.objects.get_or_create(user=request.user)
        player_game, created = PlayerGame.objects.get_or_create(player=player,
            game=game)
        if player_game.rules_accepted:
            return HttpResponseRedirect(reverse('game',
                kwargs={'game_id': game_id}))
        return render(request, self.template_name, {'game_id' : game_id})
