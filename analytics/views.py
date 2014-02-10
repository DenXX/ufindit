
from datetime import datetime

from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
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

class DataView(View):
    template_name = 'data.csv'

    def get(self, request, game_id):
        context = {}
        games = PlayerGame.objects.filter(game__id=game_id)
        header = ['id', 'start', 'finish', 'time_sec', 'score', 'extra_flags', 'liked', 'repeat', 'difficult', 'hints_useful', 'experience', 'comments']
        for i in xrange(games[0].game.tasks.count()):
            header.append('task' + str(i) + '_start')
            header.append('task' + str(i) + '_finish')
            header.append('task' + str(i) + '_time')
            header.append('task' + str(i) + '_answer')
            header.append('task' + str(i) + '_incorrect')
        data = [header, ]
        for game in games:
            survey = GameSurvey.objects.filter(player_game=game)[0] if GameSurvey.objects.filter(player_game=game).count() == 1 else None
            game_data = [game.id, game.start, game.finish, (game.finish - game.start).seconds if game.finish else None, game.score, game.extra_flags, survey.liked if survey else None, 
                survey.repeat if survey else None, survey.difficult if survey else None, survey.hints_useful if survey else None,
                survey.experience if survey else None, survey.comments if survey else None,
            ]
            for task in PlayerTask.objects.filter(player_game=game).extra(order_by=['order',]):
                game_data.append(task.start)
                game_data.append(task.finish)
                game_data.append((task.start - task.finish).seconds if task.start and task.finish else None)
                game_data.append(task.answer)
                game_data.append(task.incorrect_answers)
            data.append(map(str, game_data))
        import csv
        import StringIO
        output = StringIO.StringIO()
        csv_writer = csv.writer(output)
        csv_writer.writerows(data)
        context['data'] = output.getvalue()
        return render(request, self.template_name, context, content_type='text/csv')

@staff_member_required
def grant_bonus_view(request, game_id):
    from ufindit.mturk import MTurkProxy
    mturk = MTurkProxy('0')
    mturk.grant_bonus(Game.objects.get(id=int(game_id)))
    return HttpResponse("OK")

@staff_member_required
def approve_view(request, game_id):
    from ufindit.mturk import MTurkProxy
    mturk = MTurkProxy('0')
    mturk.approve_assignments(Game.objects.get(id=int(game_id)))
    return HttpResponse("OK")

@staff_member_required
def block_rejected_view(request, game_id):
    from ufindit.mturk import MTurkProxy
    mturk = MTurkProxy('0')
    mturk.block_rejected_users(Game.objects.get(id=int(game_id)))
    return HttpResponse("OK")