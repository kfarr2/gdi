from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from .surveys.models import Survey
from .surveys.forms import SurveyForm

def home(request):
    survey = Survey.objects.get(pk=1)
    form = SurveyForm(survey=survey)
    return render(request, 'survey.html', {
        'form': form,
    })
