# Python 2.6 doesn't have OrderedDict in the collections module
try:
    from ordereddict import OrderedDict 
except ImportError:
    # but Python 3.3 does, so we're gonna do that instead
    from collections import OrderedDict

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.contrib import messages
from mentoring.surveys.models import Survey, Question, Response
from mentoring.surveys.forms import SurveyForm
from mentoring.matches.decorators import staff_member_required
from mentoring.utils import UnicodeWriter
from .models import buildResponseQuestionLookupTable, score, Mentee, Mentor, Match, Settings
from .forms import SettingsForm

@staff_member_required
def manage(request):
    return render(request, 'manage/manage.html', {
    })

@staff_member_required
def match(request):
    mentor_responses = list(Mentor.objects.getResponses())
    mentee_responses = list(Mentee.objects.getRespones())

    results = []
    # for each mentor, mentee pair, score them together
    for mentee_response in mentee_responses:
        results.append([])
        for mentor_response in mentor_responses:
            q = buildResponseQuestionLookupTable(mentee_response, mentor_response)
            s = score(q, mentor_response)

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

    if Settings.objects.default().send_email:
        messages.warning(request, 'Email notifications are turned on!')

    mentors = list(Mentor.objects.all().select_related("user").order_by("user__last_name", "user__first_name"))
    return render(request, "manage/matches.html", {
        "results": results,
        "mentee_responses": mentee_responses,
        "mentor_responses": mentor_responses,
        "unmatched_mentees": unmatched_mentees,
        "engagements": engagements,
        "marriages": marriages,
        "mentors": mentors,
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
    messages.success(request, 'Pair engaged')
    return HttpResponseRedirect(reverse("manage-match"))

@staff_member_required
def breakup(request):
    mentor_id = request.POST.get("mentor_id")
    mentee_id = request.POST.get("mentee_id")
    Match.objects.breakup(mentor_id, mentee_id)
    messages.success(request, 'Pair broken up')
    return HttpResponseRedirect(reverse("manage-match"))

@staff_member_required
def marry(request):
    mentor_id = request.POST.get("mentor_id")
    mentee_id = request.POST.get("mentee_id")
    Match.objects.marry(mentor_id, mentee_id)
    messages.success(request, 'Pair married')
    return HttpResponseRedirect(reverse("manage-match"))

@staff_member_required
def divorce(request):
    mentor_id = request.POST.get("mentor_id")
    mentee_id = request.POST.get("mentee_id")
    Match.objects.divorce(mentor_id, mentee_id)
    messages.success(request, 'Pair divorced')
    return HttpResponseRedirect(reverse("manage-match"))

@staff_member_required
def complete(request):
    mentor_id = request.POST.get("mentor_id")
    mentee_id = request.POST.get("mentee_id")
    Match.objects.complete(mentor_id, mentee_id)
    messages.success(request, 'Pair completed')
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
        messages.success(request, 'Object deleted')
        return HttpResponseRedirect(reverse("manage-ments"))
    else:
        obj = model.objects.get(pk=request.GET['id'])
        return render(request, "manage/confirm.html", {
            "object": obj,
        })

@staff_member_required
def settings(request):
    instance = Settings.objects.default()

    if request.POST:
        form = SettingsForm(request.POST, instance=instance)
        if form.is_valid():
            messages.success(request, 'Settings updated')
            form.save()
            return HttpResponseRedirect(reverse("manage-settings"))
    else:
        form = SettingsForm(instance=instance)

    return render(request, 'manage/settings.html', {
        'form': form,
    })


@staff_member_required
def report(request):
    # someone cleverer than me could do this all in one query
    mentors = list(Mentor.objects.all().select_related('user'))
    mentees = list(Mentee.objects.all().select_related('user'))
    matches = list(Match.objects.all().order_by('engaged_on', 'married_on', 'completed_on'))

    # index everything by id
    mentor_lookup = OrderedDict()
    for mentor in mentors:
        mentor.mentees = []
        mentor.match_info = []
        mentor_lookup[mentor.pk] = mentor

    mentee_lookup = OrderedDict()
    for mentee in mentees:
        mentee_lookup[mentee.pk] = mentee

    for match in matches:
        mentor = mentor_lookup[match.mentor_id]
        mentor.mentees.append(mentee_lookup[match.mentee_id])
        mentor.match_info.append(match)

    http_response = HttpResponse()
    http_response = HttpResponse(content_type='text/csv')
    http_response['Content-Disposition'] = 'attachment; filename="report.csv"' 

    writer = UnicodeWriter(http_response)
    writer.writerow(['Mentor Name', 'Mentor Username', 'Mentee Name', 'Mentee Username', 'Matched On', 'Finalized On', 'Completed On'])

    for k, mentor in mentor_lookup.items():
        writer.writerow([mentor.user.get_full_name(), mentor.user.username])
        for i, mentee in enumerate(mentor.mentees):
            match_info = mentor.match_info[i]
            engaged_on = match_info.engaged_on or ''
            if engaged_on: engaged_on = engaged_on.strftime("%Y-%m-%d %H:%M:%S")
            married_on = match_info.married_on or ''
            if married_on: married_on = married_on.strftime("%Y-%m-%d %H:%M:%S")
            completed_on = match_info.completed_on or ''
            if completed_on: completed_on = completed_on.strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow(["", "", mentee.user.get_full_name(), mentee.user.username, engaged_on, married_on, completed_on])

    return http_response

