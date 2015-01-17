"""

This file tests everything having to do with matches except for their effects
when mixed with gasoline and fire. That gets tested in utils.

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
from .models import Mentor, Mentee, Match


class MatchTest(MentoringBaseTest):
    """
    Test views related to matches.
    """
    def setUp(self):
        super(MatchTest, self).setUp()

    def test_manage_view(self):
        # test for unauthorized n00bs
        response = self.client.get(reverse('manage'))
        self.assertEqual(response.status_code, 302)

        # test for authorized G's
        self.client.login(username=self.admin.username, password='foo')
        response = self.client.get(reverse('manage'))
        self.assertEqual(response.status_code, 200)

    def test_match_view(self):
        self.client.login(username=self.admin.username, password='foo')
        response = self.client.get(reverse('manage-match'))
        self.assertEqual(response.status_code, 200)

    def test_completions_view(self):
        self.client.login(username=self.admin.username, password='foo')
        response = self.client.get(reverse('manage-completions'))
        self.assertEqual(response.status_code, 200)

    def test_ments_view(self):
        self.client.login(username=self.admin.username, password='foo')
        response = self.client.get(reverse('manage-ments'))
        self.assertEqual(response.status_code, 200)

    def test_engage_view(self):
        data={
            'mentor_id':self.mentor.pk,
            'mentee_id':self.mentee.pk,
        }
        self.client.login(username=self.admin.username, password='foo')
        response = self.client.post(reverse('matches-engage'), data=data)
        self.assertRedirects(response, reverse('manage-match'))

    def test_marry_view(self):
        data={
            'mentor_id':self.mentor.pk,
            'mentee_id':self.mentee.pk,
        }
        self.client.login(username=self.admin.username, password='foo')
        response = self.client.post(reverse('matches-marry'), data=data)
        self.assertRedirects(response, reverse('manage-match'))

    def test_breakup_view(self):
        data={
            'mentor_id':self.mentor.pk,
            'mentee_id':self.mentee.pk,
        }
        self.client.login(username=self.admin.username, password='foo')
        response = self.client.post(reverse('matches-breakup'), data=data)
        self.assertEqual(response.status_code, 302)

    def test_divorce_view(self):
        data={
            'mentor_id':self.mentor.pk,
            'mentee_id':self.mentee.pk,
        }
        self.client.login(username=self.admin.username, password='foo')
        response = self.client.post(reverse('matches-divorce'), data=data)
        self.assertRedirects(response, reverse('manage-match'))
