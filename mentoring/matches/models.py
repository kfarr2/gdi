from django.db import models
from django.contrib.auth.models import User
from mentoring.surveys.models import ResponseQuestion, Question, Response

MENTOR_SURVEY_PK = 1
MENTEE_SURVEY_PK = 2

class Match(models.Model):
    match_id = models.AutoField(primary_key=True)
    mentor = models.ForeignKey(User, related_name="+")
    mentee = models.ForeignKey(User, related_name="+")
    matched_on = models.DateTimeField(auto_now_add=True)
    notified_on = models.DateTimeField(default=None, blank=True)

class Mentor(object):
    def __init__(self, response):
        self.response = response
        self.number_of_mentees = 0

class Mentee(object):
    def __init__(self, response):
        self.response = response

    def scoreWith(self, mentor):
        q = merge(self.response, mentor.response)
        return score(q)

    def findSuitors(self, mentors):
        suitors = []
        for mentor in mentors:
            s = self.scoreWith(mentor)
            suitors.append((mentor, s))
        suitors.sort(key=lambda pair: (-pair[1], pair[0].number_of_mentees))

        return suitors[0:3]

def getMentorResponses():
    return list(getResponses(MENTOR_SURVEY_PK))

def getMenteeRespones():
    return list(getResponses(MENTEE_SURVEY_PK))

def getResponses(survey_id):
    rows = Response.objects.raw("""
        SELECT * FROM response
        INNER JOIN (
            SELECT MAX(response_id) AS response_id FROM response 
            WHERE survey_id = %s
            GROUP BY user_id
        ) k USING(response_id)
    """, (survey_id,))
    return rows

def merge(response_a, response_b):
    rows = ResponseQuestion.objects.raw("""
        SELECT
            *,
            IF(response_question.choice_id IS NULL, response_question.value, choice.value) AS value
        FROM
            response_question
        LEFT JOIN
            choice
        ON
            response_question.choice_id = choice.choice_id
        INNER JOIN
            question
        ON 
            question.question_id = response_question.question_id
        WHERE
            response_id = %s OR response_id = %s
    """, (response_a.pk, response_b.pk))

    q = {}
    for row in rows:
        if row.question_id not in q:
            q[row.question_id] = row
            if row.type == Question.CHECKBOX:
                row.values = [row.value]
        else:
            # only checkbox questions should show up here, but we check anyways
            if row.type == Question.CHECKBOX:
                q[row.question_id].values.append(row.value)

    return q

def score(q):
    score = 0
    # check field of study
    mentee_pref = q[51].value
    mentor_pref = q[19].value
    have_same_field_of_study = q[17].value == q[49].value

    if mentee_pref == mentor_pref == "within" and have_same_field_of_study:
        # both have same field of study, and want that
        score += 2 # extra point since they both agree
    elif mentee_pref == mentor_pref == "outside" and not have_same_field_of_study:
        # both want outside field of study, and don't share the same field of study
        score += 2 # extra point for agreement
    elif mentee_pref == mentor_pref == "-1":
        # both don't care
        score += 1
    elif set([mentee_pref, mentor_pref]) == set(["-1", "within"]) and have_same_field_of_study:
        # one wants within field of study, the other doesn't care, and they
        # share field of study
        score += 1
    elif set([mentee_pref, mentor_pref]) == set(["-1", "outside"]) and not have_same_field_of_study:
        # one wants outside field of study, the other doesn't care, and they
        # don't have the same field
        score += 1

    # check gender
    mentee_pref = q[52].value
    mentor_pref = q[20].value
    mentee_gender = q[45].value
    mentor_gender = q[13].value

    if mentee_pref == mentor_pref == mentee_gender == mentor_gender == "male":
        score += 2 # extra point for mutual agreement
    elif mentee_pref == mentor_pref == mentee_gender == mentor_gender == "female":
        score += 2 # extra point for mutual agreement
    elif mentee_pref == mentor_pref == "-1":
        score += 1
    elif set([mentee_pref, mentor_pref]) == set(["-1", "male"]) and mentee_gender == mentor_gender == "male":
        score += 1
    elif set([mentee_pref, mentor_pref]) == set(["-1", "female"]) and mentee_gender == mentor_gender == "female":
        score += 1

    # check availability
    mentee_availability = int(q[53].value)
    mentor_availability = int(q[21].value)
    # if the mentor can be available the same amount or more than the mentee
    # wants, it is a good match
    if mentor_availability >= mentee_availability:
        score += 1

    # areas the mentee wants to be mentored in
    want_to_be_mentored_in = q[55].values
    for q_id in want_to_be_mentored_in:
        q_id = int(q_id)
        mentor_skill_level = int(q[q_id].value)
        # if the mentor rates himself 3 or above on the likert, it is a good match
        if mentor_skill_level >= 3:
            score += 1

    # interests
    mentee_interests = set(q[30].values)
    mentor_interests = set(q[57].values)
    if (mentee_interests & mentor_interests) != set():
        # if they have at least one thing in common, give a point for that.
        # We don't give a point for each interest, because this field seems
        # less important to me than the other ones, and shouldn't affect the
        # results too much
        score += 1

    return score
