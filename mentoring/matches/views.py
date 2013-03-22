from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.core.urlresolvers import reverse
from mentoring.surveys.models import Survey, Question, Response
from mentoring.surveys.forms import SurveyForm
from .models import merge, score, getMentorResponses, getMenteeRespones, Mentee, Mentor, Match

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
            try:
                s = score(q)
            except:
                raise ValueError(mentee.pk, mentor.pk)
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

    unmatched_mentees = list(Mentee.objects.unmatched())
    suitors = list(Mentor.objects.withMenteeCount())
    for mentee in unmatched_mentees:
        mentee.suitors = mentee.findSuitors(suitors)

    engagements = Match.objects.byMentor(married=False)
    marriages = Match.objects.byMentor(married=True)

    return render(request, "matches.html", {
        "results": results,
        "mentees": mentees,
        "mentors": mentors,
        "unmatched_mentees": unmatched_mentees,
        "engagements": engagements,
        "marriages": marriages,
    })

def engage(request):
    mentor_id = request.POST.get("mentor_id")
    mentee_id = request.POST.get("mentee_id")
    Match.objects.engage(mentor_id, mentee_id)
    return HttpResponseRedirect(reverse("matches-match"))

def breakup(request):
    mentor_id = request.POST.get("mentor_id")
    mentee_id = request.POST.get("mentee_id")
    Match.objects.breakup(mentor_id, mentee_id)
    return HttpResponseRedirect(reverse("matches-match"))

def marry(request):
    mentor_id = request.POST.get("mentor_id")
    mentee_id = request.POST.get("mentee_id")
    Match.objects.marry(mentor_id, mentee_id)
    return HttpResponseRedirect(reverse("matches-match"))

def divorce(request):
    mentor_id = request.POST.get("mentor_id")
    mentee_id = request.POST.get("mentee_id")
    Match.objects.divorce(mentor_id, mentee_id)
    return HttpResponseRedirect(reverse("matches-match"))

def removeMentor(request):
    Mentor.objects.get(pk=request.POST.get("mentor_id")).delete()
    return HttpResponseRedirect(reverse("matches-match"))

def removeMentee(request):
    Mentee.objects.get(pk=request.POST.get("mentee_id")).delete()
    return HttpResponseRedirect(reverse("matches-match"))

