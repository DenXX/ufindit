from django.contrib import admin
from querydifficulty.models import QueryDifficulty, Survey, QueryUrlProblem

admin.site.register(QueryUrlProblem)
admin.site.register(QueryDifficulty)
admin.site.register(Survey)
