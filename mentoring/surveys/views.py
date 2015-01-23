from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .models import Survey, Question, Response
from .forms import SurveyForm, MenteeSurveyForm
from mentoring.matches.models import Mentor, Mentee
from mentoring.matches.decorators import staff_member_required
from mentoring.matches.models import Settings
from mentoring.utils import UnicodeWriter


@login_required
def mentee(request):
    survey = get_object_or_404(Survey, pk=settings.MENTEE_SURVEY_PK)
    if request.method == "POST":
        form = MenteeSurveyForm(request.POST, survey=survey)
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
        form = MenteeSurveyForm(survey=survey)

    return render(request, 'surveys/mentee.html', {
        'form': form,
        'Question': Question,
    })

@login_required
def mentor(request):
    survey = get_object_or_404(Survey, pk=settings.MENTOR_SURVEY_PK)
    if request.method == "POST":
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
    message = Settings.objects.default().end_of_survey_message
    return render(request, "surveys/done.html", {
        'message': message,
    })

@staff_member_required
def response(request, response_id):
    response = get_object_or_404(Response, pk=response_id)
    report = list(response.report())
    return render(request, "surveys/response.html", {
        'response': response,
        'report': report,
        'Question': Question,
    })

@staff_member_required
def report(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    responses = list(survey.report())
    questions = list(Question.objects.filter(survey=survey).exclude(type=Question.HEADING))

    http_response = HttpResponse()
    http_response = HttpResponse(content_type='text/csv')
    http_response['Content-Disposition'] = 'attachment; filename="%s.csv"' % (survey.name)

    writer = UnicodeWriter(http_response)
    header = ["name", "username", "submitted on"] + [question.body for question in questions]
    writer.writerow(header)

    for response in responses:
        csv_row = []
        for i, question in enumerate(questions):
            row = response.get(question.pk, None)
            if i == 0:
                csv_row.append(row.name)
                csv_row.append(row.username)
                csv_row.append(row.created_on.strftime("%Y-%m-%d %H:%M:%S"))

            if row is None:
                csv_row.append("!")
                continue

            if hasattr(row, 'choice_rows'):
                csv_row.append(",".join(row.choice_rows))
            else:
                csv_row.append(row.choice_body)
        writer.writerow(csv_row)

    return http_response

