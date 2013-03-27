import json
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
            # associate the DB question with the form question so we can access
            # the DB question later
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
                # associated with it (for example, an "Other" option would
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
                cache_choices=True,
            )
        elif question.type == Question.SELECT_MULTIPLE:
            # special field type so <optgroup> tags are used
            item = NestedModelMultipleChoiceField(
                widget=forms.SelectMultiple, 
                queryset=Choice.objects.filter(question=question),
                label=question.body,
            )
        elif question.type == Question.RADIO:
            item = forms.ModelChoiceField(
                widget=RadioSelect,
                queryset=Choice.objects.filter(question=question),
                label=question.body,
                empty_label=None,
                cache_choices=True,
            )
        elif question.type == Question.SELECT:
            item = forms.ModelChoiceField(
                queryset=Choice.objects.filter(question=question),
                label=question.body,
                empty_label="",
                cache_choices=True,
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
            item = HeadingField(label=question.body, required=False)
        elif question.type == Question.TEXTAREA:
            item = forms.CharField(min_length=0, max_length=5000, required=False, label=question.body, widget=forms.Textarea)

        return item

    def clean(self):
        cleaned = super(SurveyForm, self).clean()
        # if a choice on a CHECKBOX or RADIO question has a subfield attached
        # to it, make that subfield required (only if that choice was chosen,
        # of course)
        for key, field in self.fields.items():
            # only look at questions_
            if not key.startswith("question_"):
                continue
            # only these field types have subquestions
            if field.question.type not in [Question.CHECKBOX, Question.RADIO]:
                continue
            # was a choice selected?
            choice = cleaned.get(key, None)
            if choice is None:
                continue

            # does this choice have a subfield?
            subfield_key = 'subquestion_%d' % (choice.pk)
            if subfield_key not in self.fields:
                continue

            # was the subfield filled out?
            if cleaned.get(subfield_key, "").strip() == "":
                self._errors[subfield_key] = self.error_class(['This field is required'])
                cleaned.pop(subfield_key)

        return cleaned

    def save(self, user):
        cleaned = self.cleaned_data
        response = Response()
        response.user = user
        response.survey = self.survey
        response.save()

        # create all the ResponseQuestion objects
        for k, field in self.fields.items():
            # ignore non question fields
            if not k.startswith("question_"): continue
            # ignore headings
            if field.question.type == Question.HEADING: continue

            # for questions with a relationship (which is determined if the
            # field has a querset attribute), we need to add the foreign key to
            # the ResponseQuestion
            if hasattr(field, 'queryset'):
                if field.question.type in [Question.CHECKBOX, Question.SELECT_MULTIPLE]:
                    choices = cleaned[k]
                else:
                    # RADIO and SELECT questions only have one choice selected
                    # by the user. But to make this code more generic, we
                    # package that into a list, so we can use a for loop to
                    # create the QuestionResponse objects
                    choices = [cleaned[k]]

                for choice in choices:
                    rq = ResponseQuestion()
                    rq.response = response
                    rq.question = field.question
                    rq.choice = choice
                    textbox_key = 'subquestion_%d' % (choice.pk,)
                    if textbox_key in cleaned:
                        rq.value = cleaned[textbox_key]
                    else:
                        rq.value = choice.value 
                    rq.save()
            else:
                # if the field doesn't have a queryset attribute, just save the
                # field's value. No foreign key needed
                rq = ResponseQuestion()
                rq.response = response
                rq.question = field.question
                rq.value = cleaned[k]
                rq.save()

        return response

class NestedModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    """This field type takes the queryset, and builds a 2D list of choices
    based on it. That allows the choices to be displayed in <optgroups> tags
    """
    def __init__(self, *args, **kwargs):
        super(NestedModelMultipleChoiceField, self).__init__(*args, **kwargs)
        self.choices = self.nestChoices(self.queryset)

    def nestChoices(self, queryset):
        choice_lookup = {}
        choices = []
        qs = list(queryset)
        # index all the choices by pk
        for choice in qs:
            choice_lookup[choice.pk] = choice

        # index all the subchoices by pk
        subchoice_lookup = {}

        for choice in qs:
            # this choice has choice choices because it starts with an [
            # character
            if choice.value.startswith("["): 
                # load the PKs of the subitems based on this choice's value
                items = json.loads(choice.value)
                # add all the subchoice PKs to the subchoice lookup table
                for pk in items: subchoice_lookup[pk] = True

                # add all the subchoices to this choice
                subchoices = [(choice_lookup[k].pk, choice_lookup[k].body) for k in items]
                choices.append((choice.body, subchoices))
            elif choice.pk not in subchoice_lookup:
                # this is just a regular, non-nested choice, so there is
                # nothing fancy to do
                choices.append((choice.pk, choice.body))

        return choices

class BlankWidget(forms.widgets.Widget):
    """Used as the wiget for HeadingFields, since nothing needs to be rendered"""
    def render(self, name, value, attrs=None):
        return u''

class HeadingField(forms.Field):
    widget = BlankWidget
    def __init__(self, *args, **kwargs):
        super(HeadingField, self).__init__(*args, **kwargs)

    def clean(self, value):
        return None

