"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
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



