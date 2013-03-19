from django import forms
from django.forms.widgets import RadioSelect
from .models import Question, Choice
from .checkbox import CheckboxSelectMultiple

class SurveyForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.survey = kwargs.pop("survey")
        super(SurveyForm, self).__init__(*args, **kwargs)

        self.questions = list(Question.objects.filter(survey=self.survey))

        lookup = {}
        for q in self.questions:
            self.fields['q_%d' % q.pk] = self.questionToFormField(q)
            lookup[q.pk] = q

        # figure out which form item will start/close a new layout
        state = 1
        for i, q in enumerate(self.questions):
            if state == 1:
                if q.layout != Question.NORMAL:
                    q.start_layout = True
                    state = 2
            elif state == 2:
                if q.layout == Question.NORMAL:
                    self.questions[i-1].stop_layout = True
                    state = 1

        # index as a dictionary
        self.questions = lookup

    def __getitem__(self, name):
        item = super(SurveyForm, self).__getitem__(name)
        pk = int(name[len("q_"):])
        item.question = self.questions[pk]
        return item

    def questionToFormField(self, question):
        if question.type == Question.TEXTBOX:
            item = forms.CharField(min_length=0, max_length=255, label=question.body)
        elif question.type == Question.CHECKBOX:
            choices = Choice.objects.filter(question=question)
            choices = [(c.pk, c.body) for c in choices]
            item = forms.TypedMultipleChoiceField(
                widget=CheckboxSelectMultiple, 
                choices=choices,
                coerce=lambda x: Choice.objects.get(pk=x),
                label=question.body,
            )
        elif question.type == Question.RADIO:
            choices = Choice.objects.filter(question=question)
            choices = [(c.pk, c.body) for c in choices]
            item = forms.TypedChoiceField(
                widget=RadioSelect,
                choices=choices,
                coerce=lambda x: Choice.objects.get(pk=x),
                label=question.body,
            )
        elif question.type == Question.SELECT:
            choices = Choice.objects.filter(question=question)
            choices = [(c.pk, c.body) for c in choices]
            item = forms.TypedChoiceField(
                choices=choices,
                coerce=lambda x: Choice.objects.get(pk=x),
                label=question.body,
            )
        elif question.type == Question.LIKERT:
            choices = (
                (0, "Poor"),
                (1, "Fair"),
                (2, "Good"),
                (3, "Very Good"),
                (4, "Excellent"),
            )
            item = forms.TypedChoiceField(label=question.body, choices=choices, widget=RadioSelect)
        elif question.type == Question.HEADING:
            item = HeadingField(label=question.body, required=False, widget=BlankWidget)
        elif question.type == Question.TEXTAREA:
            item = forms.CharField(min_length=0, max_length=5000, label=question.body, widget=forms.Textarea)

        return item

class BlankWidget(forms.widgets.Widget):
    def render(self, name, value, attrs=None):
        return u''

class HeadingField(forms.Field):
    def __init__(self, *args, **kwargs):
        super(HeadingField, self).__init__(*args, **kwargs)

    def clean(self, value):
        return None

