
from django.shortcuts import render, get_object_or_404
from django.views.generic.base import View
from django.views.generic import ListView

from ufindit.models import PlayerGame

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