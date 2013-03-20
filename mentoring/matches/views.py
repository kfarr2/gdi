from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.core.urlresolvers import reverse
from mentoring.surveys.models import Survey, Question, Response
from mentoring.surveys.forms import SurveyForm
from .models import merge, score, MENTOR_SURVEY_PK, MENTEE_SURVEY_PK

def match(request):
    mentors = list(Response.objects.filter(survey_id=MENTOR_SURVEY_PK))
    mentees = list(Response.objects.filter(survey_id=MENTEE_SURVEY_PK))

    results = []
    for mentee in mentees:
        results.append([])
        for mentor in mentors:
            results[-1].append({
                "mentor": mentor,
                "mentee": mentee,
                "score": score(merge(mentee, mentor))
            })


    return render(request, "matches.html", {
        "results": results,
        "mentees": mentees,
        "mentors": mentors,
    })
