# Python 2.6 doesn't have OrderedDict in the collections module
from ordereddict import OrderedDict 
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
    rank = models.IntegerField(help_text="This determines the order of this question on the survey. The lowest numbered question appears first on the survey, the second lowest numbered question appears second on the survey, etc")
    body = models.TextField(blank=True)
    hide_label = models.BooleanField(default=False, blank=True, verbose_name="Hide body", help_text="Remove the body field from this question. You might want to do this if there is a heading right before this question")
    required = models.BooleanField(default=True, blank=True, help_text="This field is required")
    layout = models.IntegerField(choices=(
        (NORMAL, "Normal"),
        (TABULAR, "Tabular"),
    ), help_text="This determines the appearance of the question on the survey.")

    survey = models.ForeignKey(Survey)

    @classmethod
    def typesWithNoChoices(cls):
        return [cls.HEADING, cls.TEXTBOX, cls.TEXTAREA, cls.LIKERT]

    @classmethod
    def isMultiValuedType(cls, type_):
        return type_ in [cls.CHECKBOX, cls.SELECT_MULTIPLE]

    @classmethod
    def couldHaveSubquestion(cls, type_):
        return type_ in [cls.CHECKBOX, cls.RADIO]

    def isMultiValued(self):
        return self.isMultiValuedType(self.type)

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
                IF(choice.body IS NULL OR choice.has_textbox, response_question.value, choice.body) AS choice_body,
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
            ORDER BY
                question.rank,
                choice.rank
        """, (self.pk, self.pk))

        # The same question can be in multiple rows because checkbox
        # and select_multiple questions have mulitple responsequestion rows
        # (one for each choice). We only want to return one question object for
        # each question, so take each choice on checkbox, and select_multiple
        # questions, and stick them into a list attached to the question object

        # we need to be able to lookup a row based on the question_id
        questions = OrderedDict()
        # for each row, check to see if it does not exists in the dict. If so,
        # add it to the dict. If it is a multivalued type (checkbox or
        # select multiple), tack on a new choice_rows attribute that is
        # appended to in the else clause
        for row in rows:
            if row.question_id not in questions:
                questions[row.question_id] = row

                if Question.isMultiValuedType(row.type):
                    # this is a checkbox or select multiple type, so it has
                    # multiple responses. So start a list of them
                    row.choice_rows = [row.choice_body]
            else:
                # we will only be in this statement if the question is a
                # checkbox or select multiple. We need to add this choice_body
                # to the existing question object
                existing_row = questions[row.question_id]
                existing_row.choice_rows.append(row.choice_body)

        return questions.values()

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
