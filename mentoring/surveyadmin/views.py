from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from mentoring.surveys.models import Survey, Question, Response, Choice
from mentoring.matches.models import Mentor, Mentee, MENTOR_SURVEY_PK, MENTEE_SURVEY_PK
from mentoring.matches.decorators import staff_member_required
from .forms import QuestionForm, ChoiceForm

@staff_member_required
def admin(request):
    surveys = Survey.objects.all()
    return render(request, 'surveyadmin/surveys.html', {
        "surveys": surveys,
    })

@staff_member_required
def questions(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    questions = Question.objects.filter(survey=survey)
    return render(request, 'surveyadmin/questions.html', {
        "survey": survey,
        "questions": questions,
    })

@staff_member_required
def question(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    survey = question.survey

    if request.POST:
        form = QuestionForm(request.POST, instance=question)
        all_valid = form.is_valid() and all([cf.is_valid() for cf in form.choiceForms()])
        # now check all the choice forms that got added dynamically with the JS
        number_of_choices = form.cleaned_data['number_of_choices']
        starting_prefix = sum(1 for _ in form.choiceForms())
        for i in range(starting_prefix, number_of_choices):
            cf = ChoiceForm(request.POST, prefix="choice_%d" % (i))
            cf.instance.question = question
            form.choice_forms.append(cf)
            all_valid &= cf.is_valid()
            if not all_valid:
                print "not valid"
                print cf._errors
                print "/not valid"

        if all_valid:
            form.save()
            for cf in form.choiceForms():
                cf.save()

            return HttpResponseRedirect(reverse('admin-surveys-questions', args=(survey.pk,)))
    else:
        form = QuestionForm(instance=question)

    return render(request, 'surveyadmin/question.html', {
        "survey": survey,
        "question": question,
        "form": form,
    })


