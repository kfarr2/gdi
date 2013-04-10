from django import forms
from mentoring.surveys.models import Survey, Question, Choice

class QuestionForm(forms.ModelForm):
    number_of_choices = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)

        # create a bunch of ChoiceForm instances for each choice on this question
        self.choice_forms = []
        choices = Choice.objects.filter(question=self.instance)
        for i, choice in enumerate(choices):
            data = None
            cf = ChoiceForm(self.data if self.is_bound else None, instance=choice, prefix="choice_%d" % (i))
            self.choice_forms.append(cf)

        self.fields['number_of_choices'].initial = len(choices)

    def choiceForms(self):
        # return all the choice forms
        for cf in self.choice_forms:
            yield cf

    def blankChoiceForm(self):
        # create a blank choice form (used in the template for making a
        # template of a choice form)
        return ChoiceForm(prefix="choice_-1")

    class Meta:
        model = Question
        exclude = ('survey', )

class ChoiceForm(forms.ModelForm):
    delete = forms.BooleanField(initial=False, required=False)

    def __init__(self, *args, **kwargs):
        super(ChoiceForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned = super(ChoiceForm, self).clean()

        # if this choice is getting deleted, who cares if it has errors
        if cleaned.get('delete', False):
            for k in self.fields:
                self.fields[k].required = False
                self._errors.pop(k, None)

        return cleaned

    def save(self, *args, **kwargs):
        if self.cleaned_data['delete']:
            if self.instance.pk is not None:
                self.instance.delete()
        else:
            super(ChoiceForm, self).save(*args, **kwargs)

    class Meta:
        model = Choice
        exclude = ('question',)
