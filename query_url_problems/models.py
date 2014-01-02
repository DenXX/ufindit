import base64
from django import forms
from django.db import models
from django.contrib.auth.models import User

from ufindit.models import Player, Serp, Task

class QueryUrlJudgement(models.Model):
    """ Judging a problem with a particular query-url """

    player = models.ForeignKey(Player, help_text=u'Player who judged the result')
    serp = models.ForeignKey(Serp, help_text=u'Which serp')
    task = models.ForeignKey(Task, help_text=u'Task for which this search was made')
    url = models.CharField(max_length=1024, help_text=u'URL of a web document')
    time = models.DateTimeField(auto_now_add=True, help_text=u'Time when user '
        'judged serp')
    judged = models.BooleanField(blank=False, default=False,
        help_text=u'True if the current pair has been already judged, i.e. '
        'one of the fields below is not empty')
    relevant = models.NullBooleanField(max_length=1024, blank=True, null=True,
        help_text=u'True if the result is relevant')
    missing_terms = models.CharField(max_length=1024,
        blank=True, null=True, help_text=u'List of terms that are '
        'missing from the results')
    misinterpreted_terms = models.CharField(max_length=1024,
        blank=True, null=True, help_text=u'List of terms that are '
        'misinterpreted in the results')
    missing_relations = models.CharField(max_length=1024,
        blank=True, null=True, help_text=u'List of term indexes relations '
        'between which are missing in the results')
    other_missing = models.CharField(max_length=1024, blank=True, null=True,
        help_text=u'Some other topic is missing')
    other_reason = models.CharField(max_length=1024, blank=True, null=True, 
        help_text=u'Some other problem')


class QueryUrlJudgementAssignment(models.Model):
    player = models.ForeignKey(Player, help_text=u'Player for this assignment')
    mturk_assignment_id = models.CharField(max_length=255, blank=True, null=True,
        help_text=u'MTurk AssignmentID')
    judgements = models.ManyToManyField(QueryUrlJudgement, help_text=u'Judgements')