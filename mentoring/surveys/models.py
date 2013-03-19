from django.db import models
from django.contrib.auth.models import User

class Survey(models.Model):
    survey_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)

    class Meta:
        db_table = "survey"

    def __unicode__(self):
        return u'%s' % (self.name)

class Question(models.Model):
    # Question types
    TEXTBOX = 1
    CHECKBOX = 2
    RADIO = 4
    SELECT = 8
    LIKERT = 16
    HEADING = 32
    TEXTAREA = 64

    # Layouts
    NORMAL = 1
    TABULAR = 2 

    question_id = models.AutoField(primary_key=True)
    type = models.IntegerField(choices=(
        (TEXTBOX, "Text"),
        (TEXTAREA, "Textarea"),
        (CHECKBOX, "Checkbox"),
        (RADIO, "Radio"),
        (SELECT, "Select"),
        (LIKERT, "Likert"),
        (HEADING, "Heading"),
    ))
    rank = models.IntegerField()
    body = models.TextField(blank=True)
    hide_label = models.BooleanField(default=False, blank=True)
    layout = models.IntegerField(choices=(
        (NORMAL, "Normal"),
        (TABULAR, "Tabular"),
    ))

    survey = models.ForeignKey(Survey)

    class Meta:
        db_table = 'question'
        ordering = ['rank']

    def __unicode__(self):
        return u'%d: %s' % (self.question_id, self.body)

class Choice(models.Model):
    choice_id = models.AutoField(primary_key=True)
    body = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    has_textbox = models.BooleanField(default=False, blank=True)
    rank = models.IntegerField()

    question = models.ForeignKey(Question)

    class Meta:
        db_table = 'choice'
        ordering = ['rank']

    def __unicode__(self):
        return u'%s' % (self.body)

class Response(models.Model):
    response_id = models.AutoField(primary_key=True)
    created_on = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey(User)
    survey = models.ForeignKey(Survey)

    class Meta:
        db_table = 'response'

class ResponseQuestion(models.Model):
    response_question_id = models.AutoField(primary_key=True)
    value = models.CharField(max_length=255)

    response = models.ForeignKey(Response)
    question = models.ForeignKey(Question)
    choice = models.ForeignKey(Choice, default=None, blank=True)

    class Meta:
        db_table = 'response_question'

class QuestionMatch(models.Model):
    question_match_id = models.AutoField(primary_key=True)
    question_a = models.ForeignKey(Question, related_name="+")
    question_b = models.ForeignKey(Question, related_name="+")

    class Meta:
        db_table = 'question_match'
