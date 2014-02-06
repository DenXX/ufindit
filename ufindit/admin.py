
from django import forms
from django.contrib import admin
from ufindit.models import *

class TaskAdminForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Task

class TaskAdmin(admin.ModelAdmin):
    form = TaskAdminForm

class PlayerTaskAdmin(admin.ModelAdmin):
    list_filter = ('finish', )

class PlayerGameAdmin(admin.ModelAdmin):
    readonly_fields = ('start',)
    list_filter = ('finish',)

class SerpAdmin(admin.ModelAdmin):
    readonly_fields = ('results_urls', )

class GameSurveyAdmin(admin.ModelAdmin):
    list_filter = ('player_game__game', 'player_game__extra_flags', 'player_game__start')

admin.site.register(Game)
admin.site.register(Task, TaskAdmin)
admin.site.register(Player)
admin.site.register(PlayerGame, PlayerGameAdmin)
admin.site.register(PlayerTask, PlayerTaskAdmin)
admin.site.register(Event)
admin.site.register(Serp, SerpAdmin)
admin.site.register(UserSerpResultsOrder)
admin.site.register(GameSurvey, GameSurveyAdmin)
