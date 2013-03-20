from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.core.urlresolvers import reverse
from mentoring.surveys.models import Survey, Question, Response
from mentoring.surveys.forms import SurveyForm
from .models import merge, score, getMentorResponses, getMenteeRespones

def match(request):
    mentors = getMentorResponses()
    mentees = getMenteeRespones()

    results = []
    # don't be hating my O(n**2) algorithm
    for mentee in mentees:
        results.append([])
        best_mentors = []
        best_score = 0
        for mentor in mentors:
            q = merge(mentee, mentor)
            s = score(q)
            if s == best_score:
                best_mentors.append(mentor)
            elif s > best_score:
                best_mentors = [mentor]

            if s >= best_score:
                best_score = s

            results[-1].append({
                "mentor": mentor,
                "mentee": mentee,
                "score": s
            })
            mentor.first_name = q[2].value
            mentor.last_name = q[3].value

        mentee.first_name = q[34].value
        mentee.last_name = q[35].value

    

    return render(request, "matches.html", {
        "results": results,
        "mentees": mentees,
        "mentors": mentors,
    })
