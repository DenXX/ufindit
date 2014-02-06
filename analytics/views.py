
from datetime import datetime

from django.shortcuts import render, get_object_or_404
from django.views.generic.base import View
from django.views.generic import ListView

from ufindit.models import *

class GamesView(ListView):
    """ A view for player games """
    model = PlayerGame
    context_object_name = 'games'
    template_name = "games_data.html"

    def get_queryset(self):
        if self.kwargs['finish'] == 'f':
            return self.model.objects.exclude(finish=None)
        else:
            return self.model.objects.all()


class GameView(View):
    template_name = 'game_data.html'

    def get(self, request, game_id):
        game = get_object_or_404(PlayerGame, id=game_id)
        return render(request, self.template_name, {'game': game})

class AnalyzeView(View):
    template_name = 'analyze.html'

    def get(self, request):
        context = {}
        allgames = PlayerGame.objects.filter(game__id=13, start__gte=datetime(year=2014, month=2, day=1))
        all_hint_games = allgames.filter(extra_flags=1)
        all_nohint_games = allgames.filter(extra_flags=0)
        context['hint_total_count'] = all_hint_games.count()
        context['nohint_total_count'] = all_nohint_games.count()

        games = PlayerGame.objects.filter(game__id=13, start__gte=datetime(year=2014, month=2, day=1), finish__isnull=False)
        context['games'] = games
        hint_games = games.filter(extra_flags=1)
        nohint_games = games.filter(extra_flags=0)
        context['hint_count'] = hint_games.count()
        context['nohint_count'] = nohint_games.count()

        time = 0
        count = 0
        times = []
        for g in hint_games:
            time += (g.finish - g.start).seconds
            times.append((g.finish - g.start).seconds)
            count += 1
        context['hint_time'] = 1.0 * time / count
        context['hint_times'] = times

        time = 0
        count = 0
        times = []
        for g in nohint_games:
            time += (g.finish - g.start).seconds
            times.append((g.finish - g.start).seconds)
            count += 1
        context['nohint_time'] = 1.0 * time / count
        context['nohint_times'] = times

        score = 0
        count = 0
        for g in hint_games:
            score += g.score
            count += 1
        context['hint_score'] = 1.0 * score / count

        score = 0
        count = 0
        for g in nohint_games:
            score += g.score
            count += 1
        context['nohint_score'] = 1.0 * score / count

        survey = []
        for g in hint_games:
            s = GameSurvey.objects.filter(player_game = g)
            survey.append(s[0].hints_useful)
        context['hint_survey'] = survey

        survey = []
        for g in nohint_games:
            s = GameSurvey.objects.filter(player_game = g)
            survey.append(s[0].hints_useful)
        context['nohint_survey'] = survey

        return render(request, self.template_name, context)