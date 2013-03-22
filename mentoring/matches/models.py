from django.db import models
from django.contrib.auth.models import User
from mentoring.surveys.models import ResponseQuestion, Question, Response

MENTOR_SURVEY_PK = 1
MENTEE_SURVEY_PK = 2

class MentorManager(models.Manager):
    def get_queryset(self):
        return super(MentorManager, self).get_queryset().filter(is_deleted=False)

    def withMenteeCount(self):
        return Mentor.objects.raw("""
            SELECT 
                mentor.*, COUNT(`match`.mentee_id) AS number_of_mentees
            FROM
                mentor
                    LEFT JOIN
                `match` USING (mentor_id)
                    LEFT JOIN
                mentee ON mentee.mentee_id = `match`.mentee_id
                    AND mentee.is_deleted = 0
            WHERE
                mentor.is_deleted = 0
            GROUP BY mentor_id
        """)

class Mentor(models.Model):
    mentor_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, related_name="+")
    response = models.ForeignKey(Response)
    is_deleted = models.BooleanField(default=False, blank=True)

    objects = MentorManager()

    class Meta:
        db_table = "mentor"

class MenteeManager(models.Manager):
    def unmatched(self):
        return Mentee.objects.raw("""
            SELECT 
                * 
            FROM 
                `match` 
            RIGHT JOIN 
                mentee 
            USING(mentee_id) 
            WHERE 
                match_id IS NULL AND 
                (`match`.is_deleted IS NULL OR `match`.is_deleted = 0) AND
                mentee.is_deleted = 0
        """)

class Mentee(models.Model):
    mentee_id = models.AutoField(primary_key=True)
    is_deleted = models.BooleanField(default=False, blank=True)

    user = models.ForeignKey(User, related_name="+")
    response = models.ForeignKey(Response)

    objects = MenteeManager()

    def scoreWith(self, mentor):
        q = merge(self.response, mentor.response)
        return score(q)

    def findSuitors(self, mentors):
        suitors = []
        for mentor in mentors:
            s = self.scoreWith(mentor)
            suitors.append((mentor, s))
        suitors.sort(key=lambda pair: (-pair[1], pair[0].number_of_mentees))

        return [s[0] for s in suitors[0:3]]

    class Meta:
        db_table = "mentee"

class MatchManager(models.Manager):
    def get_queryset(self):
        return super(MatchManager, self).get_queryset().filter(is_deleted=False)
    
    def byMentor(self):
        rows = Match.objects.raw("""
            SELECT 
                * 
            FROM 
                `match`
            INNER JOIN 
                mentee 
            ON 
                match.mentee_id = mentee.mentee_id
            INNER JOIN 
                mentor 
            ON 
                match.mentor_id = mentor.mentor_id
            WHERE 
                mentee.is_deleted = 0 AND 
                mentor.is_deleted = 0 AND 
                match.is_deleted = 0
        """)
        return rows

class Match(models.Model):
    match_id = models.AutoField(primary_key=True)
    mentor = models.ForeignKey(Mentor, related_name="+")
    mentee = models.ForeignKey(Mentee, related_name="+")
    matched_on = models.DateTimeField(auto_now_add=True)
    notified_on = models.DateTimeField(null=True, default=None, blank=True)
    is_deleted = models.BooleanField(default=False, blank=True)

    objects = MatchManager()

    class Meta:
        db_table = "match"

def getMentorResponses():
    return Response.objects.raw("""
    SELECT * FROM mentor INNER JOIN response USING(response_id) WHERE mentor.is_deleted = 0
    """)

def getMenteeRespones():
    return Response.objects.raw("""
    SELECT * FROM mentee INNER JOIN response USING(response_id) WHERE mentee.is_deleted = 0
    """)

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
