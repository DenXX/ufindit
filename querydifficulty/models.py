import base64
from django import forms
from django.db import models
from django.contrib.auth.models import User

from ufindit.models import Serp, PlayerTask

class QueryDifficulty(models.Model):
    player_task = models.ForeignKey(PlayerTask)
    serp = models.ForeignKey(Serp, help_text=u'Search engine results')
    time = models.DateTimeField(auto_now_add=True, help_text=u'Time when user '
        'judged serp')
    panelDwellTime = models.PositiveIntegerField(help_text=u'How long did user '
        'look at the query difficulty panel')
    difficulty = models.TextField(help_text=u'Type of difficulty')

    def __unicode__(self):
        return self.player_task.player_game.player.user.username + " - " + \
            self.serp.query
