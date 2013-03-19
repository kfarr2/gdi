from django.contrib import admin
from .models import *

class ChoiceInline(admin.TabularInline):
    model = Choice

class QuestionAdmin(admin.ModelAdmin):
    inlines = [
        ChoiceInline,
    ]

admin.site.register(Survey)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice)
admin.site.register(Response)
admin.site.register(ResponseQuestion)
admin.site.register(QuestionMatch)
