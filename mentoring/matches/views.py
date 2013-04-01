from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.contrib.admin.views.decorators import staff_member_required
from mentoring.surveys.models import Survey, Question, Response
from mentoring.surveys.forms import SurveyForm
from .models import buildResponseQuestionLookupTable, score, Mentee, Mentor, Match

@staff_member_required
def manage(request):
    return render(request, 'manage/manage.html', {
    })

@staff_member_required
def match(request):
    mentor_responses = Mentor.objects.getResponses()
    mentee_responses = Mentee.objects.getRespones()

    results = []
    # for each mentor, mentee pair, score them together
    for mentee_response in mentee_responses:
        results.append([])
        for mentor_response in mentor_responses:
            q = buildResponseQuestionLookupTable(mentee_response, mentor_response)
            s = score(q)

            results[-1].append({
                "mentor_response": mentor_response,
                "mentee_response": mentee_response,
                "score": s
            })

    # find the best suitors for each unmatched mentee
    unmatched_mentees = list(Mentee.objects.unmatched())
    suitors = list(Mentor.objects.withMenteeCount())
    for mentee in unmatched_mentees:
        mentee.suitors = mentee.findSuitors(suitors)

    engagements = Match.objects.byMentor(married=False)
    marriages = Match.objects.byMentor(married=True)

    return render(request, "manage/matches.html", {
        "results": results,
        "mentee_responses": mentee_responses,
        "mentor_responses": mentor_responses,
        "unmatched_mentees": unmatched_mentees,
        "engagements": engagements,
        "marriages": marriages,
    })

@staff_member_required
def completions(request):
    completed = Match.objects.byMentor(married=True, completed=True)
    return render(request, "manage/completions.html", {
        "completed": completed,
    })

@staff_member_required
def ments(request):
    mentors = Mentor.objects.all().select_related("user")
    mentees = Mentee.objects.all().select_related("user")
    return render(request, 'manage/ments.html', {
        "mentors": mentors,
        "mentees": mentees,
    })

@staff_member_required
def engage(request):
    mentor_id = request.POST.get("mentor_id")
    mentee_id = request.POST.get("mentee_id")
    Match.objects.engage(mentor_id, mentee_id)
    return HttpResponseRedirect(reverse("manage-match"))

@staff_member_required
def breakup(request):
    mentor_id = request.POST.get("mentor_id")
    mentee_id = request.POST.get("mentee_id")
    Match.objects.breakup(mentor_id, mentee_id)
    return HttpResponseRedirect(reverse("manage-match"))

@staff_member_required
def marry(request):
    mentor_id = request.POST.get("mentor_id")
    mentee_id = request.POST.get("mentee_id")
    Match.objects.marry(mentor_id, mentee_id)
    return HttpResponseRedirect(reverse("manage-match"))

@staff_member_required
def divorce(request):
    mentor_id = request.POST.get("mentor_id")
    mentee_id = request.POST.get("mentee_id")
    Match.objects.divorce(mentor_id, mentee_id)
    return HttpResponseRedirect(reverse("manage-match"))

@staff_member_required
def complete(request):
    mentor_id = request.POST.get("mentor_id")
    mentee_id = request.POST.get("mentee_id")
    Match.objects.complete(mentor_id, mentee_id)
    return HttpResponseRedirect(reverse("manage-match"))

@staff_member_required
def remove(request, object_name):
    if object_name == "mentors":
        model = Mentor
    elif object_name == "mentees":
        model = Mentee
    else:
        raise ValueError("%s is not 'mentors' or 'mentees'" % (object_name,))

    if request.POST:
        model.objects.get(pk=request.POST.get('id')).delete()
        return HttpResponseRedirect(reverse("manage"))
    else:
        obj = model.objects.get(pk=request.GET['id'])
        return render(request, "manage/confirm.html", {
            "object": obj,
        })
