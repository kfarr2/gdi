import csv, codecs
from io import StringIO
from django.contrib.auth.models import User
from django.test import TestCase
from mentoring.matches.models import Mentor, Mentee
from mentoring.surveys.models import Survey, Question, Choice, Response, ResponseQuestion

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


#TODO: Get more default models set up
class MentoringBaseTest(TestCase):
    """
    A base test that all other tests will use.

    """
    def setUp(self):
        super(MentoringBaseTest, self).setUp()
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

        # Make a survey 
        s = Survey(
            name='Test Survey',
        )
        s.save()
        self.survey = s

        # Make a question
        q = Question(
            type=0, # Text type question
            rank=1,
            body='Nobody inspects the spammish repitition.',
            hide_label=False,
            required=False,
            layout=0, # Normal layout
            survey=self.survey,
        )
        q.save()
        self.question = q

        # Make a choice
        c = Choice(
            body='Nobody inspects the spammish repitition.',
            value='Do not press',
            has_textbox=True,
            rank=1,
            question=self.question,
        )
        c.save()
        self.choice = c


        # Make a response

        # Make a response question

        # Make a mentor using Admin
        m = Mentor(
            is_deleted=False,
            user=self.admin,

        )


