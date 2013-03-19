from django import forms

class SurveyForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.survey = kwargs.pop("survey")
        super(SurveyForm, self).__init__(*args, **kwargs)
