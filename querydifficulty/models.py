import base64
from django import forms
from django.db import models
from django.contrib.auth.models import User

from ufindit.models import Serp, PlayerTask, PlayerGame

class QueryUrlProblem(models.Model):
    """
        Information on problem with a particular serp result
    """

    player_task = models.ForeignKey(PlayerTask)
    serp = models.ForeignKey(Serp, help_text=u'Search engine results')
    doc_rank = models.PositiveSmallIntegerField(help_text=u'The rank of the '
        'document')
    time = models.DateTimeField(auto_now_add=True, help_text=u'Time when user '
        'judged serp')
    missing_terms = models.CommaSeparatedIntegerField(max_length=1024,
        blank=True, null=True, help_text=u'List of term indexes which are '
        'missing from the results')
    misinterpreted_terms = models.CommaSeparatedIntegerField(max_length=1024,
        blank=True, null=True, help_text=u'List of term indexes which are '
        'misinterpreted in the results')
    missing_relations = models.CommaSeparatedIntegerField(max_length=1024,
        blank=True, null=True, help_text=u'List of term indexes relations '
        'between which are missing in the results')
    extra = models.CharField(max_length=512, blank=True, null=True, 
        help_text=u'Extra information on the problem with the query')

    def __unicode__(self):
        return self.player_task.player_game.player.user.username + " - " + \
            self.serp.query + "( " + str(self.doc_rank) + " )"


class QueryDifficulty(models.Model):
    """
        Information on problem with the whole search result page
    """
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


class Survey(models.Model):
    """
        Survey at the end of the game
    """
    player_game = models.ForeignKey(PlayerGame)
    liked = models.IntegerField(help_text=u'How did user like the game '
        '(from -2..2)')
    repeat = models.IntegerField(help_text=u'How likely will user play again '
        '(from -2..2)')
    difficult = models.IntegerField(help_text=u'How difficult the game was '
        '(from -2..2)')
    distracting = models.IntegerField(help_text=u'How distracting was it to answer '
        'questions on what didn\'t you like in search results?')
    qdiffEasy = models.IntegerField(help_text=u'How easy was it to answer '
        'questions on what didn\'t you like in search results?')
    qdiffComment = models.TextField(blank=True, null=True, help_text=u'User '
        'comments on query difficulty questions')
    comments = models.TextField(blank=True, null=True, help_text=u'User '
        'comments on the game')


    def __unicode__(self):
        return u'Survey: ' + unicode(self.player_game)