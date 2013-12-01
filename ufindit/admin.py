from django.contrib import admin
from ufindit.models import Game, Task, Player, PlayerGame, PlayerTask, Event, Serp, UserSerpResultsOrder

admin.site.register(Game)
admin.site.register(Task)

admin.site.register(Player)
admin.site.register(PlayerGame)
admin.site.register(PlayerTask)
admin.site.register(Event)
admin.site.register(Serp)
admin.site.register(UserSerpResultsOrder)