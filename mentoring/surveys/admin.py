from django.contrib import admin
from .models import *

class ChoiceInline(admin.TabularInline):
    model = Choice

class QuestionInline(admin.TabularInline):
    model = Question

class QuestionAdmin(admin.ModelAdmin):
    inlines = [
        ChoiceInline,
    ]

class SurveyAdmin(admin.ModelAdmin):
    inlines = [
        QuestionInline,
    ]

admin.site.register(Survey, SurveyAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice)
admin.site.register(Response)
admin.site.register(ResponseQuestion)
