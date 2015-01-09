"""

This file should test everything having to do with the Surveys application.
It will not contain tests for models as they will be handled in the utils.py
file.
Written by Konstantin, but if anything goes wrong, it was Sean.

"""

from django.test import TestCase
from mentoring.utils.tests import MentoringBaseTest
from .forms import SurveyForm
from .models import Survey

#TODO: finish survey forms & views tests
class SurveyFormsTest(MentoringBaseTest):
    """
    Test all forms in the surveys app
    """
    def setUp(self):
        super(SurveyFormsTest, self).setUp()
        self.client.login(username=self.admin.username, password=self.admin.password)

    def test_invalid_survey_form(self):
        form = SurveyForm(survey=self.survey)
        self.assertFalse(form.is_valid())

    #TODO: finish this test
    def test_valid_survey_form(self):
        count = Survey.objects.count()
        form = SurveyForm(
            survey=self.survey,
        )
