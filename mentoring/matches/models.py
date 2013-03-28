from collections import defaultdict, namedtuple
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
        """Return a list of namedtuples of potential mentors and their scores,
        ordered by the mentee's preference for the mentor"""
        Pair = namedtuple('Pair', 'mentor score')
        suitors = []
        for mentor in mentors:
            s = self.scoreWith(mentor)
            # keep track of the mentor, and the score with that mentor
            suitors.append(Pair(mentor, s))

        # sort by the score first obviously, and for equal scores, order by the
        # number of mentees (since a mentor with fewer mentees is preferred)
        suitors.sort(key=lambda pair: (-pair.score, pair.mentor.number_of_mentees))

        # return the first 3 mentor picks
        return suitors[0:3]

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
            if Question.isMultiValuedType(row.type):
                row.values = [row.value]
        else:
            # if we're in this branch, it MUST be a checkbox, or select
            # multiple question, or there is a bug somewhere.
            if Question.isMultiValuedType(row.type):
                # append the value for this ResponseQuestion to the list of
                # values
                question_values[row.question_id].values.append(row.value)

    # convert to q QuestionDict
    return QuestionDict(question_values)

class QuestionDict(dict):
    """This dict will return an object of type BlankItem when the key to the
    dict does not exist in __getitem__.

    This helps to avoid KeyErrors in the score function.
    """

    class BlankItem(object):
        def __init__(self):
            self.value = None
            self.values = []

    def __getitem__(self, key):
        return self.get(key, self.BlankItem())

def score(q):
    """Using the QuestionDict from buildResponseQuestionLookupTable(), score the
    results"""

    # the magic numbers you see in this function indexing the q dictionary are
    # the question_ids from the surveys

    ###########
    # Weights #
    ###########

    # they share a preferred field of study
    MATCHING_FIELD_OF_STUDY_PREFERENCE = 10
    # they match on their preferred gender
    MATCHING_GENDER_PREFERENCE = 5
    # there is a match on gender, *but* one person doesn't care about gender
    MATCHING_GENDER_ONE_SIDED = 3
    # both don't care about gender
    MATCHING_GENDER_APATHY = 0
    # the mentor is available as much as the mentee wants
    MATCHING_AVAILABILITY = 3
    # skill points (the key is the question_id from the mentor form, value is
    # the amount of points to award for a match)
    MATCHING_SKILL = {
        23: 2, # Teaching techniques
        24: 2, # networking
        25: 2, # tenue review
        68: 2, # promotion to full profship
        69: 2, # moving to tenure track
        70: 2, # become admin
        26: 2, # research
        27: 2, # time management
        28: 2, # work life balance
        65: 2, # navigating psu
        66: 2, # faculty of color
        67: 2, # publication
    }
    # they have an interest in common
    MATCHING_INTERESTS = 1

    # the mentee already has someone in mind
    if q[61].value == "yes":
        return -1

    score = 0

    # check field of study
    mentee_pref = q[51].values
    mentor_pref = q[19].values
    mentor_fields_of_study = q[17].values
    mentee_fields_of_study = q[49].values

    matches_mentee_pref = bool(set(mentee_pref) & set(mentor_fields_of_study)) 
    matches_mentor_pref = bool(set(mentor_pref) & set(mentee_fields_of_study))
    if matches_mentee_pref and matches_mentor_pref:
        score += 10

    # check gender
    mentee_pref = q[52].value
    mentor_pref = q[20].value
    mentee_gender = q[45].value
    mentor_gender = q[13].value

    if (mentee_pref == mentor_gender) and (mentor_pref == mentee_gender):
        score += MATCHING_GENDER_PREFERENCE
    elif mentee_pref == mentor_pref == "-1":
        score += MATCHING_GENDER_APATHY
    elif (mentee_pref == mentor_gender) and mentor_pref == "-1":
        score += MATCHING_GENDER_ONE_SIDED
    elif (mentor_pref == mentee_gender) and mentee_pref == "-1":
        score += MATCHING_GENDER_ONE_SIDED

    # check availability
    mentee_availability = int(q[53].value)
    mentor_availability = int(q[21].value)
    # if the mentor can be available the same amount or more than the mentee
    # wants, it is a good match
    if mentor_availability >= mentee_availability:
        score += MATCHING_AVAILABILITY

    # areas the mentee wants to be mentored in
    want_to_be_mentored_in = q[55].values
    # the values of q[55] are indices to the likert question_ids, so we use
    # those to lookup the corresponding question
    for q_id in want_to_be_mentored_in:
        q_id = int(q_id)
        mentor_skill_level = int(q[q_id].value)
        # if the mentor rates himself 3 or above on the likert, it is a good match
        if mentor_skill_level >= 3:
            score += MATCHING_SKILL[q_id]

    # interests
    mentee_interests = set(q[30].values)
    mentor_interests = set(q[57].values)
    if (mentee_interests & mentor_interests) != set():
        # if they have at least one thing in common, give a point for that.
        # We don't give a point for each interest, because this field seems
        # less important to me than the other ones, and shouldn't affect the
        # results too much
        score += MATCHING_INTERESTS

    return score
