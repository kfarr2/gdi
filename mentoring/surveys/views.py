from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from .models import Survey, Question
from .forms import SurveyForm

def survey(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    if request.POST:
        form = SurveyForm(request.POST, survey=survey)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("surveys-done"))
    else:
        form = SurveyForm(survey=survey)

    return render(request, 'surveys/survey.html', {
        'form': form,
        'Question': Question,
    })

def done(request):
    return render(request, "surveys/done.html", {

    })
