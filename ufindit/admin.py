
from django import forms
from django.contrib import admin
from ufindit.models import Game, Task, Player, PlayerGame, PlayerTask, Event, Serp, UserSerpResultsOrder

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

admin.site.register(Game)
admin.site.register(Task, TaskAdmin)
admin.site.register(Player)
admin.site.register(PlayerGame, PlayerGameAdmin)
admin.site.register(PlayerTask, PlayerTaskAdmin)
admin.site.register(Event)
admin.site.register(Serp)
admin.site.register(UserSerpResultsOrder)
