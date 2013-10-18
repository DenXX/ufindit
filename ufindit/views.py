from datetime import datetime
from search_proxy import SearchProxy
from urllib import unquote

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404

from httpproxy.views import HttpProxy
from ufindit.forms import RegistrationForm
from ufindit.logger import EventLogger
from ufindit.models import Game, Player, PlayerGame, PlayerTask

import settings

def index(request):
    context = {}
    context["games"] = Game.objects.filter(active = True)
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
def search(request, task_id, template='serp.html'):
    context = {"task_id":task_id}
    user = request.user
    player = Player.objects.get(user=request.user)
    player_task = get_object_or_404(PlayerTask, id=task_id)
    if "q" in request.GET:
        query = unquote(request.GET["q"]).decode('utf8')
        EventLogger.query(player_task, query)
        search_proxy = SearchProxy(settings.SEARCH_PROXY)
        context["query"] = query
        search_results = search_proxy.search(query)
        context["serpid"] = search_results.id
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
    context["enable_emu"] = settings.ENABLE_EMU_LOGGING
    return render(request, template, context)


@login_required
def game(request, game_id):
    game = get_object_or_404(Game, id=game_id, active=True)
    player, _ = Player.objects.get_or_create(user=request.user)
    player_game, _ = PlayerGame.objects.get_or_create(player=player, game=game)
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
        return HttpResponseRedirect(reverse('game', kwargs={'game_id':game_id}))

    context = { "game" : game, "player_task": current_task }
    return render(request, 'game.html', context)


def http_proxy_decorator(request, task_id, url):
    player_task = get_object_or_404(PlayerTask, id=task_id)
    EventLogger.click(player_task, url)
    return HttpResponseRedirect(reverse('http_proxy', kwargs={'url':url,
        'task_id':task_id}))
