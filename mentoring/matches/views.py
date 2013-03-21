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

    unmatched_mentees = list(Mentee.objects.unmatched())
    suitors = list(Mentor.objects.withMenteeCount())
    for mentee in unmatched_mentees:
        mentee.suitors = mentee.findSuitors(suitors)

    matches = Match.objects.byMentor()

    return render(request, "matches.html", {
        "results": results,
        "mentees": mentees,
        "mentors": mentors,
        "unmatched_mentees": unmatched_mentees,
        "matches": matches,
    })

def marry(request):
    mentor_id = request.POST.get("mentor_id")
    mentee_id = request.POST.get("mentee_id")

    m = Match()
    m.mentor = Mentor.objects.get(pk=mentor_id)
    m.mentee = Mentee.objects.get(pk=mentee_id)
    m.save()
    return HttpResponseRedirect(reverse("matches-match"))

def divorce(request):
    mentor_id = request.POST.get("mentor_id")
    mentee_id = request.POST.get("mentee_id")
    Match.objects.get(mentor_id=mentor_id, mentee_id=mentee_id).delete()
    return HttpResponseRedirect(reverse("matches-match"))
