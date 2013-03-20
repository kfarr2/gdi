from django import forms
from django.forms.widgets import RadioSelect
from django.contrib.auth.models import User
from .models import Question, Choice, Response, ResponseQuestion
from .checkbox import CheckboxSelectMultiple

class SurveyForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.survey = kwargs.pop("survey")
        super(SurveyForm, self).__init__(*args, **kwargs)

        questions = list(Question.objects.filter(survey=self.survey))
        # add all the fields for each question
        for q in questions:
            item = self.questionToFormField(q)
            item.question = q
            self.fields['question_%d' % q.pk] = item

            # because the choices for a checkbox or radio button can have an
            # optional textfield associated with it, we need to add that
            # "subquestion" to the form
            if q.type in [Question.CHECKBOX, Question.RADIO]:
                choices = item.queryset.all()
                for c in choices:
                    if c.has_textbox:
                        field = forms.CharField(required=False, min_length=0, max_length=255)
                        self.fields['subquestion_%d' % c.pk] = field

        # figure out which form item will start/close a new layout.
        # This is helpful because in a template, we need to create the opening
        # <table> and closing </table> tags when rendering a tabular layout 
        state = 1
        for i, q in enumerate(questions):
            if state == 1:
                # find the beginning of a non-normal question layout
                if q.layout != Question.NORMAL:
                    # mark the question as starting the layout
                    q.start_layout = True
                    state = 2
            elif state == 2:
                # find the end of the non-normal question layout 
                if q.layout == Question.NORMAL:
                    # mark the *previous* question to stop the non-normal layout
                    questions[i-1].stop_layout = True
                    state = 1

    def questionFields(self):
        """Return the list of question fields for the form"""
        for k in self.fields:
            if k.startswith("question_"):
                item = self[k]
                # add the question object to the boundfield
                item.question = self.fields[k].question

                # because CHECKBOX and RADIO choices can have an extra field
                # associated with it (for example, an "Option" option would
                # have a textbox where the user would fill something in)
                # we need to tack on the "subquestion" in a convient place, so
                # it is easily rendered in the template
                if item.question.type in [Question.CHECKBOX, Question.RADIO]:
                    choice_fields = []
                    choices = list(self.fields[k].queryset)
                    for field, choice in zip(item, choices):
                        if choice.has_textbox:
                            # tack on the extra textbox field for this choice
                            field.textbox = self['subquestion_%d' % choice.pk]
                        choice_fields.append(field)
                    item.choices = choice_fields

                yield item

    def questionToFormField(self, question):
        """Generate a form field for a question"""
        if question.type == Question.TEXTBOX:
            item = forms.CharField(min_length=0, max_length=255, label=question.body)
        elif question.type == Question.CHECKBOX:
            item = forms.ModelMultipleChoiceField(
                widget=CheckboxSelectMultiple, 
                queryset=Choice.objects.filter(question=question),
                label=question.body,
            )
        elif question.type == Question.RADIO:
            item = forms.ModelChoiceField(
                widget=RadioSelect,
                queryset=Choice.objects.filter(question=question),
                label=question.body,
                empty_label=None,
            )
        elif question.type == Question.SELECT:
            item = forms.ModelChoiceField(
                queryset=Choice.objects.filter(question=question),
                label=question.body,
                empty_label="",
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
            item = forms.CharField(min_length=0, max_length=5000, required=False, label=question.body, widget=forms.Textarea)

        return item

    def save(self, user):
        cleaned = self.cleaned_data
        response = Response()
        response.user = user
        response.survey = self.survey
        response.save()

        for k, field in self.fields.items():
            # ignore non question fields
            if not k.startswith("question_"): continue
            # ignore headings
            if field.question.type == Question.HEADING: continue

            if hasattr(field, 'queryset'):
                if field.question.type != Question.CHECKBOX:
                    choices = [cleaned[k]]
                else:
                    choices = cleaned[k]

                for choice in choices:
                    rq = ResponseQuestion()
                    rq.response = response
                    rq.question = field.question
                    rq.choice = choice
                    rq.value = choice.value 
                    rq.save()
            else:
                rq = ResponseQuestion()
                rq.response = response
                rq.question = field.question
                rq.value = cleaned[k]
                rq.save()


class BlankWidget(forms.widgets.Widget):
    def render(self, name, value, attrs=None):
        return u''

class HeadingField(forms.Field):
    def __init__(self, *args, **kwargs):
        super(HeadingField, self).__init__(*args, **kwargs)

    def clean(self, value):
        return None

