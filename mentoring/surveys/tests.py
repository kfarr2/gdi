"""

This file should test everything having to do with the Surveys application.
It will not contain tests for models as they will be handled in utils/tests.py.
Written by Konstantin, but if anything goes wrong, it was Sean.

"""
from unittest import mock
from unittest.mock import patch
from model_mommy.mommy import make
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.test import TestCase
from mentoring.utils.tests import MentoringBaseTest
from mentoring.matches.models import Mentor, Mentee
from .forms import SurveyForm, MenteeSurveyForm
from .models import Survey, ResponseQuestion, Response
from .views import survey, mentee, mentor, done, response, report
from .checkbox import CheckboxSelectMultiple, CheckboxInput, CheckboxRenderer

class SurveyFormsTest(MentoringBaseTest):
    """
    Test most forms in the surveys app.
    There are a lot that have to do with formatting
    that seem unnecessary to test.
    """
    def setUp(self):
        super(SurveyFormsTest, self).setUp()
        self.client.login(username=self.admin.username, password=self.admin.password)

    def test_invalid_survey_form(self):
        form = SurveyForm(survey=self.survey)
        self.assertFalse(form.is_valid())

    def test_valid_survey_form(self):
        form = SurveyForm(
            survey=self.survey,
            data={
                "question_2": self.question,
            }
        )
        self.assertTrue(form.is_valid())
        count = ResponseQuestion.objects.count()
        form.save(self.admin)
        self.assertEqual(count + 1, ResponseQuestion.objects.count())

    def test_invalid_mentee_survey_form(self):
        form = MenteeSurveyForm(
            survey=self.survey,
        )
        self.assertFalse(form.is_valid())

    def test_valid_mentee_survey_form(self):
        form = MenteeSurveyForm(
            survey=self.survey,
            data={
                "question_61": self.choice,
            }
        )
        self.assertTrue(form.is_valid())
        count = Response.objects.count()
        form.save(self.admin)
        self.assertEqual(count + 1, Response.objects.count())


class SurveyViewsTest(MentoringBaseTest):
    """
    Test views in the surveys application
    """

    def setUp(self):
        super(SurveyViewsTest, self).setUp()
        self.client.logout()

    # Gonna skip testing this because the view seems to never be used.
    """
    def test_survey_get_without_login(self):
        self.client.get(reverse('survey'))
    """


    # Mentee views
    def test_mentee_get_without_login(self):
        response = self.client.get(reverse('surveys-mentee'))
        self.assertEqual(response.status_code, 302)

    def test_mentee_get(self):
        self.client.login(username=self.admin.username, password=self.password)
        settings.MENTEE_SURVEY_PK = self.survey.pk
        response = self.client.get(reverse('surveys-mentee'))
        self.assertEqual(response.status_code, 200)

    def test_mentee_invalid_post(self):
        self.client.login(username=self.admin.username, password=self.password)
        settings.MENTEE_SURVEY_PK = self.survey.pk
        with patch('mentoring.surveys.forms.MenteeSurveyForm.is_valid', return_value=False) as data:
            with patch('mentoring.surveys.forms.MenteeSurveyForm.save', return_value=True):
                response = self.client.post(reverse('surveys-mentee'), data)
        self.assertEqual(response.status_code, 200)

    def test_mentee_valid_post(self):
        self.client.login(username=self.admin.username, password=self.password)
        settings.MENTEE_SURVEY_PK = self.survey.pk
        with patch('mentoring.surveys.forms.MenteeSurveyForm.is_valid', return_value=True) as data:
            with patch('mentoring.surveys.forms.MenteeSurveyForm.save', return_value=self.response):
                response = self.client.post(reverse('surveys-mentee'), data)
        self.assertEqual(response.status_code, 302)


    # Mentor views
    def test_mentor_get(self):
        self.client.login(username=self.admin.username, password=self.password)
        settings.MENTOR_SURVEY_PK = self.survey.pk
        response = self.client.get(reverse('surveys-mentor'))
        self.assertEqual(response.status_code, 200)

    def test_mentor_invalid_post(self):
        self.client.login(username=self.admin.username, password=self.password)
        settings.MENTOR_SURVEY_PK = self.survey.pk
        with patch('mentoring.surveys.forms.SurveyForm.is_valid', return_value=False) as data:
            with patch('mentoring.surveys.forms.SurveyForm.save', return_value=True):
                response = self.client.post(reverse('surveys-mentor'), data)
        self.assertEqual(response.status_code, 200)

    def test_mentor_valid_post(self):
        self.client.login(username=self.admin.username, password=self.password)
        settings.MENTOR_SURVEY_PK = self.survey.pk
        with patch('mentoring.surveys.forms.SurveyForm.is_valid', return_value=True) as data:
            with patch('mentoring.surveys.forms.SurveyForm.save', return_value=self.response):
                response = self.client.post(reverse('surveys-mentor'), data)
        self.assertEqual(response.status_code, 302)

    # Other views
    def test_done_view(self):
        self.client.login(username=self.admin.username, password=self.password)
        response = self.client.get(reverse('surveys-done'))
        self.assertEqual(response.status_code, 200)

    def test_response_view(self):
        self.client.login(username=self.admin.username, password=self.password)
        response = self.client.get(reverse('surveys-response', args=[self.response.pk,]))
        self.assertEqual(response.status_code, 200)

    def test_report_view(self):
        self.client.login(username=self.admin.username, password=self.password)
        response = self.client.get(reverse('surveys-report', args=[self.survey.pk,]))
        data = 'attachment; filename="%s.csv"' % (self.survey.name)
        self.assertTrue(response['Content-Disposition'], data)


class CheckboxTest(MentoringBaseTest):
    """
    Tests having to do with checkbox.py
    
    This may be a little unnecessary to write tests for 
    as it's almost all rendering stuff
    """
    def setUp(self):
        super(CheckboxTest, self).setUp()
        #checkbox_renderer = CheckboxRenderer()
        #checkbox_multiple = CheckboxSelectMultiple()
