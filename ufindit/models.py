import base64
from django.db import models
from django.contrib.auth.models import User


class Player(models.Model):
    user = models.OneToOneField(User)
    mturk_worker_id = models.CharField(max_length=100, blank=True, null=True,
        help_text=u'ID of the user in Mechanical Turk or null')

    def __unicode__(self):
        return self.user.email + \
            (' (' + self.mturk_worker_id + ')' if self.mturk_worker_id else '')


class Task(models.Model):
    text = models.CharField(max_length=1024, help_text=u"Text of a search task")

    def __unicode__(self):
        return self.text[0:min(50, len(self.text))]


class Game(models.Model):
    name = models.CharField(max_length=255, default="", blank=True,
        help_text=u"Name of the game")
    tasks = models.ManyToManyField(Task, related_name='task+',
        help_text=u"Game tasks")
    active = models.BooleanField(default=False,
        help_text=u'Is the game active/shown in the list')
    randomized = models.BooleanField(default=False,
        help_text=u'Are game questions randomized for each participant')

    def __unicode__(self):
        return self.name


class PlayerGame(models.Model):
    player = models.ForeignKey(Player)
    game = models.ForeignKey(Game)
    start = models.DateTimeField(auto_now_add=True,
        help_text=u'Start time of the game')
    last_activity = models.DateTimeField(auto_now=True,
        help_text=u'Last activity in the game')
    current_task_index = models.PositiveIntegerField(default=0,
        help_text=u'The index of the current task. '
            'Index by order in PlayerTask')
    finish = models.DateTimeField(blank=True, null=True,
        help_text=u'End time of the game')

    def save(self, *args, **kwargs):
        created = not self.pk
        super(PlayerGame, self).save(*args, **kwargs)
        # If object is being created, create PlayerTasks as well.
        if created:
            tasks_count = self.game.tasks.count()
            order = range(tasks_count)
            if self.game.randomized:
                from random import shuffle
                shuffle(order)
            for index, task in enumerate(self.game.tasks.all()):
                ptask = PlayerTask.objects.create(player_game=self, task=task,
                    order=order[index])
                ptask.save()

    def __unicode__(self):
        return unicode(self.game) + ' (' + self.player.user.email + ')'


class PlayerTask(models.Model):
    player_game = models.ForeignKey(PlayerGame)
    task = models.ForeignKey(Task)
    order = models.PositiveIntegerField(db_index=True, help_text=u'Order of '
        'the task in the game for the current user')
    start = models.DateTimeField(blank=True, null=True, help_text=u'Start time '
        'of the task')
    finish = models.DateTimeField(blank=True, null=True, help_text=u'Finish '
        'time of the task')
    answer = models.CharField(max_length=1024, blank=True, null=True, 
        help_text=u'User answer to the task')
    answer_url = models.URLField(blank=True, null=True, help_text=u'URL of '
        'a web page with the answer')

    def __unicode__(self):
        return self.task.text + u' [%s - %d]' % (self.player_game.player.user.email, 
            self.order)

    class Meta:
        ordering = ['order']


class Event(models.Model):
    player_task = models.ForeignKey(PlayerTask)
    event = models.CharField(max_length=10, db_index=True, help_text=u'Type of '
        'event: Query, Click, Answer, etc.')
    time = models.DateTimeField(auto_now_add=True, help_text=u'Time when event '
        'happened')
    query = models.CharField(max_length=1024, blank=True, null=True,
        help_text=u'Query text if the event is query')
    serp = models.ForeignKey(Serp, blank=True, null=True, help_text=u'SERP')
    url = models.URLField(blank=True, null=True, help_text=u'Clicked url')
    extra_data = models.TextField(blank=True, null=True,
        help_text=u'Extra information about the event')

    def __unicode__(self):
        return self.event + ': ' + (self.query if self.query else '') + \
            (self.url if self.url else '') + ' (' + str(self.time) + ')'

    class Meta:
        ordering = ['player_task', 'time']


class Serp(models.Model):
    query = models.CharField(max_length=1024, db_index=True,
        help_text=u'Text of the query')
    engine = models.CharField(max_length=10, db_index=True,
        help_text=u'Code of search engine used')
    _results = models.TextField(db_column='results', help_text=u'Base64 encoded '
        'pickled Results list')

    def set_results(self, results):
        self._results = base64.encodestring(results)

    def get_results(self):
        return base64.decodestring(self._results)

    results = property(get_results, set_results)

    def __unicode__(self):
        return self.query

    class Meta:
        unique_together = ("query", "engine")


class QueryDifficulty(models.Model):
    player_task = models.ForeignKey(PlayerTask)
    serp = models.ForeignKey(Serp, help_text=u'Search engine results')
    difficulty = models.CharField(max_length=512, help_text=u'Type of difficulty')

    def __unicode__(self):
        return self.player_task.player_game.player.user.username + " - " + self.serp.query
