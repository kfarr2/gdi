from unittest import mock
from unittest.mock import patch
from model_mommy.mommy import make
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.test import TestCase, Client 
from mentoring.utils.tests import MentoringBaseTest
from mentoring.matches.models import Mentor, Mentee
from mentoring.surveys.models import Choice
from .forms import QuestionForm, ChoiceForm


class SurveyAdminFormsTest(MentoringBaseTest):
    """
    This class tests all forms in the surveyadmin application
    """
    def setUp(self):
        super(SurveyAdminFormsTest, self).setUp()

    def test_invalid_choice_form(self):
        cf = ChoiceForm()
        self.assertFalse(cf.is_valid())

    def test_valid_choice_form(self):
        old_choice_body = self.choice.body
        cf = ChoiceForm(
            instance=self.choice,
            data={
                'body':'Lol js-fiddle is great',
                'value':'a partridge in a pear tree',
                'has_textbox':False,
                'rank':1,
                'delete':False
            },
        )
        self.assertTrue(cf.is_valid())
        count = Choice.objects.count()
        cf.save()
        self.assertIsNot(old_choice_body, self.choice.body)
        self.assertEqual(count, Choice.objects.count())

    def test_invalid_question_form(self):
        qf = QuestionForm()
        self.assertFalse(qf.is_valid())

    def test_valid_question_form(self):
        qf = QuestionForm(
            data={
                'number_of_choices':1,
                'type':4,
                'rank':1,
                'body':'Whats going on here',
                'hide_body':True,
                'required':True,
                'layout':2,
            }
        )
        self.assertTrue(qf.is_valid())


class SurveyAdminViewsTest(MentoringBaseTest):
    """
    This class tests all views in the surveyadmin application
    """
    def setUp(self):
        super(SurveyAdminViewsTest, self).setUp()

    def test_admin_view(self):
        # unauthorized user
        response = self.client.get(reverse('admin-surveys'))
        self.assertEqual(response.status_code, 302)
        # authorized user
        self.client.login(username=self.admin.username, password='foo')
        response = self.client.get(reverse('admin-surveys'))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_questions_view(self):
        question_pk = self.question.pk
        # Unauthorized User
        response = self.client.get(reverse('admin-surveys-questions', args=(question_pk,)))
        self.assertEqual(response.status_code, 302)
        # Authorized User
        self.client.login(username=self.admin.username, password='foo')
        response = self.client.get(reverse('admin-surveys-questions', args=(self.question.pk,)))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_question_view(self):
        question_pk = self.question.pk
        self.client.login(username=self.admin.username, password='foo')
        # Test get
        response = self.client.get(reverse('admin-surveys-question', args=(question_pk,)))
        self.assertEqual(response.status_code, 200)
        # Test invalid post
        data={
            'number_of_choices':1,
            'type':4,
            'rank':1,
            'body':'Whats going on here',
        }
        response = self.client.post(reverse('admin-surveys-question', args=(question_pk,)), data=data)
        self.assertEqual(response.status_code, 200)

        # Test valid post
        data = {
            'number_of_choices':1,
            'type':32,
            'rank':100,
            'body':'Whats going on here',
            'hide_body':True,
            'required':False,
            'layout':2,
            'choice_0-body':'a',
            'choice_0-value':'a',
            'choice_0-has_textbox':True,
            'choice_0-rank':1,
            'choice_0-delete':False,
        }
        response = self.client.post(reverse('admin-surveys-question', args=(question_pk,)), data=data)
        self.assertEqual(response.status_code, 302)
        self.client.logout()

