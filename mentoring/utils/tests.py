import csv, codecs
from io import StringIO
from django.contrib.auth.models import User
from django.test import TestCase
from mentoring.matches.models import Mentor, Mentee, Match
from mentoring.surveys.models import Survey, Question, Choice, Response, ResponseQuestion
from mentoring.matches.models import Settings


class MentoringBaseTest(TestCase):
    """
    A base test that all other tests will use.

    """
    def setUp(self):
        self.make_user_models()
        self.make_survey_models()
        self.make_response_models()
        self.make_mentor_models()
        super(MentoringBaseTest, self).setUp()

    def make_user_models(self):
        # making a default password to use for all instances of users
        self.password = "foo"

        # Make an admin
        a = User(
            first_name='Rango',
            last_name='Mango',
            username='FruitLizard111',
            is_staff=True,
        )
        a.set_password(self.password)
        a.save()
        self.admin = a

        # Make a regular ol' user
        u = User(
            first_name='Alice',
            last_name='Inchains',
            username='MetalHeadTillImDead',
            is_staff=False,
        )
        u.set_password(self.password)
        u.save()
        self.user = u

    def make_survey_models(self):
        # Make a survey
        s = Survey(
            name='Test Survey',
        )
        s.save()
        self.survey = s

        # Make another survey
        s = Survey(
            name='Test Survey The Sequel',
        )
        s.save()
        self.survey_2 = s
        self.assertEqual(str(s), s.name)

        # Make a question
        q = Question(
            type=1, # Checkbox type question
            rank=1,
            body='Nobody inspects the spammish repitition.',
            hide_label=False,
            required=False,
            layout=1, # Normal layout
            survey=self.survey,
        )
        q.save()
        self.question = q

        # Make a question
        q = Question(
            type=1, # Checkbox type question
            rank=1,
            body='Nobody inspects the spammish repitition.',
            hide_label=False,
            required=False,
            layout=1, # Normal layout
            survey=self.survey_2,
        )
        q.save()
        self.question_2 = q

        # Make a choice
        c = Choice(
            body='Nobody inspects the spammish repitition.',
            value='yes',
            has_textbox=False,
            rank=1,
            question=self.question,
        )
        c.save()
        self.choice = c

    def make_response_models(self):
        # Make a response
        r = Response(
            user=self.admin,
            survey=self.survey,
        )
        r.save()
        self.response = r

        # Make another response
        r = Response(
            user=self.user,
            survey=self.survey_2,
        )
        r.save()
        self.response_2 = r

        # Make a response question
        rq = ResponseQuestion(
            value='Nobody inspects the spammish repitition.',
            response=self.response,
            question=self.question,
            choice=self.choice,
        )
        rq.save()
        self.response_question = rq

        # Make a response question
        rq = ResponseQuestion(
            value='Nobody inspects the spammish repitition.',
            response=self.response_2,
            question=self.question_2,
            choice=self.choice,
        )
        rq.save()
        self.response_question_2 = rq

    def make_mentor_models(self):
        s = Settings(

        )
        s.save()
        self.settings = s

        # Make a mentor using Admin
        m = Mentor(
            is_deleted=False,
            user=self.admin,
            response=self.response,
        )
        m.save()
        self.mentor = m

        # Make a manatee using a regular user
        m = Mentee(
            is_deleted=False,
            user=self.admin,
            response=self.response_2,
        )
        m.save()
        self.mentee = m

        # Be a matchmaker
        m = Match(
            mentor=self.mentor,
            mentee=self.mentee,
            is_deleted=False,
        )
        m.save()
        self.match = m

