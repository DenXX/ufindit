from django.contrib import admin
from ufindit.models import Game, Task, Player, PlayerGame, PlayerTask, Event

admin.site.register(Game)
admin.site.register(Task)

admin.site.register(Player)
admin.site.register(PlayerGame)
admin.site.register(PlayerTask)

admin.site.register(Event)