from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from .surveys.models import Survey, Question
from .surveys.forms import SurveyForm

def home(request):
    survey = Survey.objects.get(pk=1)
    if request.POST:
        form = SurveyForm(request.POST, survey=survey)
        if form.is_valid():
            form.save()
            return HttpResponse("valid")
    else:
        form = SurveyForm(survey=survey)

    return render(request, 'surveys/survey.html', {
        'form': form,
        'Question': Question,
    })
