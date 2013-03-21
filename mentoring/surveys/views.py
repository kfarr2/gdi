from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from .models import Survey, Question
from .forms import SurveyForm
from mentoring.matches.models import Mentor, Mentee, MENTOR_SURVEY_PK, MENTEE_SURVEY_PK

@login_required
def survey(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    if request.POST:
        form = SurveyForm(request.POST, survey=survey)
        if form.is_valid():
            form.save(user=request.user)
            return HttpResponseRedirect(reverse("surveys-done"))
    else:
        form = SurveyForm(survey=survey)

    return render(request, 'surveys/survey.html', {
        'form': form,
        'Question': Question,
    })

@login_required
def mentee(request):
    survey = get_object_or_404(Survey, pk=MENTEE_SURVEY_PK)
    if request.POST:
        form = SurveyForm(request.POST, survey=survey)
        if form.is_valid():
            response = form.save(user=request.user)
            # create the mentee object, or update it
            try:
                mentee = Mentee.objects.get(user=request.user)
            except Mentee.DoesNotExist as e:
                mentee = Mentee()
                mentee.user = request.user

            mentee.response = response
            mentee.save()
            return HttpResponseRedirect(reverse("surveys-done"))
    else:
        form = SurveyForm(survey=survey)

    return render(request, 'surveys/survey.html', {
        'form': form,
        'Question': Question,
    })

@login_required
def mentor(request):
    survey = get_object_or_404(Survey, pk=MENTOR_SURVEY_PK)
    if request.POST:
        form = SurveyForm(request.POST, survey=survey)
        if form.is_valid():
            response = form.save(user=request.user)

            # create the mentor object, or update it
            try:
                mentor = Mentor.objects.get(user=request.user)
            except Mentor.DoesNotExist as e:
                mentor = Mentor()
                mentor.user = request.user

            mentor.response = response
            mentor.save()

            return HttpResponseRedirect(reverse("surveys-done"))
    else:
        form = SurveyForm(survey=survey)

    return render(request, 'surveys/survey.html', {
        'form': form,
        'Question': Question,
    })

@login_required
def done(request):
    return render(request, "surveys/done.html", {

    })
