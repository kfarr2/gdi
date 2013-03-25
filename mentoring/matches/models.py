from collections import defaultdict
from datetime import datetime
from django.db import models
from django.contrib.auth.models import User
from mentoring.surveys.models import ResponseQuestion, Question, Response

MENTOR_SURVEY_PK = 1
MENTEE_SURVEY_PK = 2

class MentorManager(models.Manager):
    def get_queryset(self):
        return super(MentorManager, self).get_queryset().filter(is_deleted=False)

    def withMenteeCount(self):
        """Return a queryset of mentors, and include the number of mentors each
        mentor mentors"""
        return Mentor.objects.raw("""
            SELECT 
                mentor.*, COUNT(`match`.mentee_id) AS number_of_mentees
            FROM
                mentor
            LEFT JOIN
                `match` USING (mentor_id)
            LEFT JOIN
                mentee 
            ON 
                mentee.mentee_id = `match`.mentee_id AND 
                mentee.is_deleted = 0
            WHERE
                mentor.is_deleted = 0
            GROUP BY mentor_id
        """)

    def getResponses(self):
        """Get the response object for each mentor"""
        return Response.objects.raw("""
            SELECT 
                * 
            FROM 
                mentor 
            INNER JOIN 
                response 
            USING(response_id) 
            WHERE 
                mentor.is_deleted = 0
        """)


class Mentor(models.Model):
    mentor_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, related_name="+")
    response = models.ForeignKey(Response)
    is_deleted = models.BooleanField(default=False, blank=True)

    objects = MentorManager()

    def delete(self):
        """Delete a mentor, and clean up loose ends"""
        user = self.user
        # remove their response questions
        ResponseQuestion.objects.filter(response__user=user, response__survey_id=MENTOR_SURVEY_PK).delete()
        # remove the response
        Response.objects.filter(user=user, survey_id=MENTOR_SURVEY_PK).delete()
        # delete any matches with this mentor
        Match.objects.filter(mentor=self).delete()
        # delete this
        super(Mentor, self).delete()

    class Meta:
        db_table = "mentor"
        ordering = ['user__date_joined']

class MenteeManager(models.Manager):
    def unmatched(self):
        """Return the mentees who have not been matched with any mentor"""
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

    def getRespones(self):
        """Return the response object for each mentee"""
        return Response.objects.raw("""
            SELECT 
                * 
            FROM 
                mentee 
            INNER JOIN 
                response 
            USING(response_id) 
            WHERE 
                mentee.is_deleted = 0
        """)

class Mentee(models.Model):
    mentee_id = models.AutoField(primary_key=True)
    is_deleted = models.BooleanField(default=False, blank=True)

    user = models.ForeignKey(User, related_name="+")
    response = models.ForeignKey(Response)

    objects = MenteeManager()

    def delete(self):
        """Delete this mentee and all the related stuff"""
        user = self.user
        # delete response questions
        ResponseQuestion.objects.filter(response__user=user, response__survey_id=MENTEE_SURVEY_PK).delete()
        # delete response itself
        Response.objects.filter(user=user, survey_id=MENTEE_SURVEY_PK).delete()
        # delete any matches with this person
        Match.objects.filter(mentee=self).delete()
        # delete the mentee
        super(Mentee, self).delete()

    def scoreWith(self, mentor):
        """Score this mentee against the passed-in mentor object"""
        q = buildResponseQuestionLookupTable(self.response, mentor.response)
        return score(q)

    def findSuitors(self, mentors):
        """Return a list of potential mentors, ordered by their preference for
        the mentor"""
        suitors = []
        for mentor in mentors:
            s = self.scoreWith(mentor)
            # keep track of the mentor, and the score with that mentor
            suitors.append((mentor, s))

        # sort by the score first obviously, and for equal scores, order by the
        # number of mentees (since a mentor with fewer mentees is preferred)
        suitors.sort(key=lambda pair: (-pair[1], pair[0].number_of_mentees))

        # return the first 3 mentor picks
        return [s[0] for s in suitors[0:3]]

    class Meta:
        db_table = "mentee"
        ordering = ['user__date_joined']

class MatchManager(models.Manager):
    def get_queryset(self):
        return super(MatchManager, self).get_queryset().filter(is_deleted=False)

    def byMentor(self, married=True, completed=False):
        """Return a list of mentors, with an added attribute called "mentees"
        containing a list of mentees the mentor is matched with"""
        where_clause = ""
        # you can tell a couple is married by the notified_on date
        if married:
            where_clause = " match.notified_on IS NOT NULL"
        else:
            where_clause = " match.notified_on IS NULL"

        # you can tell a couple is completed by the completed_on date
        if completed:
            where_clause += " AND match.completed_on IS NOT NULL "
        else:
            where_clause += " AND match.completed_on IS NULL "

        rows = Mentor.objects.raw("""
            SELECT
                mentee.mentee_id,
                mentor.mentor_id,
                auth_user.username AS mentor_username,
                auth_user2.username as mentee_username
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
            INNER JOIN
                auth_user
            ON 
                mentor.user_id = auth_user.id 
            INNER JOIN 
                auth_user auth_user2
            ON 
                mentee.user_id = auth_user2.id
            WHERE
                mentee.is_deleted = 0 AND
                mentor.is_deleted = 0 AND
                match.is_deleted = 0 AND
                """ + where_clause)

        
        mentors_lookup = defaultdict(list)
        # for each row, see who the mentor is, and add it to the dictionary if
        # it doesn't exist in there yet. Then add the special "mentees"
        # attribute to the mentor object, and append the row to it
        for row in rows:
            # these mentor exists in the lookup table already, so just add this
            # row to the list of mentees
            if row.mentor_id in mentors_lookup:
                mentors_lookup[row.mentor_id].mentees.append(row)
            else:
                # need to create the mentees attribute, initialize it with the
                # current row, and add to the lookup table
                row.mentees = [row]
                mentors_lookup[row.mentor_id] = row

        # return the list of mentors
        return mentors_lookup.values()

    def marry(self, mentor_id, mentee_id):
        """Marry the mentor with the mentee"""
        m = Match.objects.get(mentor_id=mentor_id, mentee_id=mentee_id)
        # simply set the notified_on date to something not null to flag the
        # match as married
        m.notified_on = datetime.now()
        m.save()

    def divorce(self, mentor_id, mentee_id):
        Match.objects.get(mentor_id=mentor_id, mentee_id=mentee_id).delete()

    def engage(self, mentor_id, mentee_id):
        m = Match()
        m.mentor = Mentor.objects.get(pk=mentor_id)
        m.mentee = Mentee.objects.get(pk=mentee_id)
        m.save()

    def breakup(self, mentor_id, mentee_id):
        Match.objects.get(mentor_id=mentor_id, mentee_id=mentee_id).delete()

    def complete(self, mentor_id, mentee_id):
        match = Match.objects.get(mentor_id=mentor_id, mentee_id=mentee_id)
        # just set the completed_on date to something to flag this match as
        # completed
        match.completed_on = datetime.now()
        match.save()

class Match(models.Model):
    match_id = models.AutoField(primary_key=True)
    mentor = models.ForeignKey(Mentor, related_name="+")
    mentee = models.ForeignKey(Mentee, related_name="+")
    matched_on = models.DateTimeField(auto_now_add=True)
    notified_on = models.DateTimeField(null=True, default=None, blank=True)
    completed_on = models.DateTimeField(null=True, default=None, blank=True)
    is_deleted = models.BooleanField(default=False, blank=True)

    objects = MatchManager()

    class Meta:
        db_table = "match"


def buildResponseQuestionLookupTable(response_a, response_b):
    """Build a dictionary where the key is a question id, and the value is the
    of the ResponseQuestion object for that question, with a special "value" or
    "values" attribute. Include the ResponseQuestion objects from the
    response_a and response_b Response objects"""

    if response_a.survey_id == response_b.survey_id:
        raise ValueError("response_a.survey_id cannot be the same as response_b.survey_id")

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

    question_values = {}
    # for each ResponseQuestion row, add it to the question_values map if it
    # doesn't exist. For checkbox questions, attach a values attribute, and
    # make it a list that includes all the values selected for that question
    for row in rows:
        if row.question_id not in question_values:
            question_values[row.question_id] = row
            # for checkbox questions, it will have a "values" attribute that is
            # a list of values selected for that question
            if row.type == Question.CHECKBOX:
                row.values = [row.value]
        else:
            # if we're in this branch, it MUST be a checkbox question, or there
            # is a bug somewhere.

            if row.type == Question.CHECKBOX:
                # append the value for this ResponseQuestion to the list of
                # values
                question_values[row.question_id].values.append(row.value)

    return question_values

def score(q):
    """Using the dictionary from buildResponseQuestionLookupTable(), score the
    results"""
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
