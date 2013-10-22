from datetime import datetime
from search_proxy import SearchProxy
from urllib import unquote

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
from ufindit.models import Game, Player, PlayerGame, PlayerTask, Serp

import settings

def index(request):
    context = RequestContext(request, 
        {'games' : Game.objects.filter(active = True)})
    return render(request, 'index.html', context)


def register(request):
    context = {}
    registration_form = RegistrationForm()
    if request.method == "POST":
        registration_form = RegistrationForm(request.POST)
        if registration_form.is_valid():
            email = registration_form.cleaned_data['email']
            if User.objects.filter(email=email).exists():
                context['errors'] = 'User with this email already exists'
                context["registration_form"] = registration_form
                return render(request, 'registration.html', context)
            password = registration_form.cleaned_data['password']
            user = User.objects.create_user(email, email, password)
            user.save()
            return render(request, 'registration.html', context)
    context["registration_form"] = registration_form
    return render(request, 'registration.html', context)


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True, max_age=0)
def search(request, task_id, template='serp.html'):
    context = {"task_id":task_id}
    user = request.user
    player = Player.objects.get(user=request.user)
    player_task = get_object_or_404(PlayerTask, id=task_id)
    if "q" in request.GET:
        query = unquote(request.GET["q"]).decode('utf8')
        search_proxy = SearchProxy(settings.SEARCH_PROXY)
        context["query"] = query
        search_results = search_proxy.search(query)
        context["serpid"] = search_results.id
        # Log query event
        serp = get_object_or_404(Serp, id=search_results.id)
        paginator = Paginator(search_results, settings.RESULTS_PER_PAGE)
        page = request.GET.get('page')
        try:
            context["results"] = paginator.page(page)
            page = int(page)
        except PageNotAnInteger:
            context["results"] = paginator.page(1)
            page = 1
        except EmptyPage:
            context["results"] = paginator.page(paginator.num_pages)
            page = paginator.num_pages
        start_page = max([1, page - 3])
        end_page = min([paginator.num_pages + 1, page + 4])
        context["page_numbers"] = range(start_page, end_page)
        # Log query event
        EventLogger.query(player_task, query, serp, context["results"].number)
    context["enable_emu"] = settings.ENABLE_EMU_LOGGING
    return render(request, template, context)


class GameView(View):
    """
        Top level page for the game. The pages shows game top panel and 
        search box in a frame. It also accepts answers and skips with POST
        requests.
    """

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
        user = self.get_mturk_user(workerId)
        login(request, user)
        return user.is_authenticated()

    def get_mturk_user(self, workerId):
        try:
            player = Player.objects.get(mturk_worker_id=workerId)
        except Player.DoesNotExist:
            user = User.objects.create_user(workerId, workerId+'@mturk.com',
                workerId)
            user.save()
            player = Player.objects.create(user=user, mturk_worker_id=workerId)
            player.save()
        user = authenticate(username=workerId+'@mturk.com', password=workerId)
        return user


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

        if player_game.current_task_index >= \
            PlayerTask.objects.filter(player_game=player_game).count():
            if not player_game.finish:
                player_game.finish = datetime.now()
                player_game.save()
            return render(request, 'game_over.html', {'game' : game})

        current_task = get_object_or_404(PlayerTask, player_game=player_game,
            order=player_game.current_task_index)
        if current_task.start == None:
            current_task.start = datetime.now()
            current_task.save()
        # Check if the task wasn't finished
        assert current_task.finish == None
        
        # If form was submitted, either skipped or answered.
        if request.method == "POST":
            return self.post(request, player_game, current_task)
        else:
            return self.get(request, game, current_task)


    def post(self, request, player_game, current_task):
        if request.POST.has_key("save_answer"):
            current_task.answer = request.POST['answer']
            current_task.answer_url = request.POST['answer_url']
        elif not request.POST.has_key("skip"):
            raise Http404
        # Save the current task
        player_game.current_task_index += 1
        player_game.save()
        current_task.finish = datetime.now()
        current_task.save()
        # Redirect back so that refresh doesn't cause form resend.
        return HttpResponseRedirect(reverse('game',
            kwargs={'game_id':player_game.game.id}))

    def get(self, request, game, current_task):
        context = { "game" : game, "player_task": current_task }
        return render(request, 'game.html', context)


def http_proxy_decorator(request, task_id, serp_id, url):
    player_task = get_object_or_404(PlayerTask, id=task_id)
    serp = get_object_or_404(Serp, id=serp_id)
    EventLogger.click(player_task, url, serp=serp)
    return HttpResponseRedirect(reverse('http_proxy', kwargs={'url':url,
        'task_id':task_id}))
