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
    SELECT_MULTIPLE = 128

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
        (SELECT_MULTIPLE, "Select Multiple"),
        (LIKERT, "Likert"),
        (HEADING, "Heading"),
    ))
    rank = models.IntegerField()
    body = models.TextField(blank=True)
    hide_label = models.BooleanField(default=False, blank=True)
    required = models.BooleanField(default=True, blank=True)
    layout = models.IntegerField(choices=(
        (NORMAL, "Normal"),
        (TABULAR, "Tabular"),
    ))

    survey = models.ForeignKey(Survey)

    class Meta:
        db_table = 'question'
        ordering = ['survey__pk', 'rank']

    def __unicode__(self):
        return u'%d: %s %s' % (self.question_id, self.survey.name, self.body)

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

    def report(self):
        rows = Question.objects.raw("""
            SELECT
                question.question_id,
                question.type,
                question.body,
                question.hide_label,
                question.layout,
                response_question.value as cached_value,
                GROUP_CONCAT(IF(choice.body IS NULL OR choice.has_textbox, response_question.value, choice.body) SEPARATOR '\n') AS choice_body,
                choice.has_textbox
            FROM
                question
            LEFT JOIN
                response_question
            ON
                response_question.question_id = question.question_id AND
                response_id = %s
            LEFT JOIN
                choice USING (choice_id)
            WHERE
                question.survey_id = (SELECT survey_id FROM response WHERE response_id = %s)
            GROUP BY question_id
            ORDER BY
                question.rank,
                choice.rank
        """, (self.pk, self.pk))
        return rows

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
