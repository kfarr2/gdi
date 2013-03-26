# DO NOT RUN THIS IF YOU DON'T KNOW WHAT YOU'RE DOING
import os
import sys
root = os.path.normpath(os.path.join(os.path.dirname(__file__), "../"))
sys.path.append(root)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mentoring.settings")

from mentoring.surveys.models import Question, Choice

fields_of_study = """Maseeh College of Engineering and Computer Science
Civil and Environmental Engineering
Computer Science
Electrical and Computer Engineering
Mechanical and Materials Engineering
Engineering and Technology Management

College of Liberal Arts and Sciences
Anthropology
Applied Linguistics
Biology
Black Studies
Center for Science Education
Chemistry
Chicano and Latino Studies
Communication
Conflict Resolution
Economics
English
Environmental Sciences and Management
Geography
Geology
History
International Studies
Judaic Studies
Mathematics
Indigenous Nations Studies Program
Philosophy
Physics
Psychology
School of the Environment
Sociology
Speech and Hearing Sciences
Women, Gender, Sexuality Studies
World Languages and Literatures

College of Urban and Public Affairs
Institution for Portland Metro Studies & Pop Res Center
School of Community Health
Hatfield School of Government
Public Administration
Toulan School of Urban Studies & Planning

School of Business Administration
Accounting
Advertising Management
Finance
Finance
Human Resources Management
Management & Leadership
Marketing
Real Estate
Supply & Logistics Management

School of Extended Studies
Extended Campus
Independent Study
Professional Development Center
Summer Session

School of Fine and Performing Arts
Art
Architecture
Music
Theater Arts

Graduate School of Education
Curriculum & Instruction
Educational Leadership & Policy
Special Education
Counselor Education

School of Social Work
Child & Family Studies
PhD Program
MSW Program
Child Welfare Partnership Program
Regional Research Institute

University Library

Office of Academic Affairs
University Honors Program
University Studies
Center for Academic Excellence/Center for Online Learning
Ronald E. McNair Program
USARMY Gold

Office of Enrollment Management and Student Affairs

Office of the Dean of Student Life

Office of Admissions, Registration, and Records

Office of Finance & Administration

Office of Human Resources

Facilities and Property Management

Campus Public Safety Office

Office of General Counsel

Office of Global Diversity and Inclusion

Office of Graduate Studies

Office of Institutional Research and Planning

Office of International Affairs

Office of Research and Strategic Partnerships

Office of University Advancement

Office of the President"""

choices = fields_of_study.split("\n\n")
for i in range(len(choices)):
    if "\n" in choices[i]:
        subchoices = choices[i].split("\n")
        heading = subchoices.pop(0)
        choices[i] = {"heading": heading, "subchoices": subchoices}

question_ids = [17, 19, 49, 51]
for question_id in question_ids:
    question = Question.objects.get(pk=question_id)
    Choice.objects.filter(question=question).delete()
    i = 0
    for choice in choices:
        if type(choice) == dict:
            parent = Choice(question=question, body=choice['heading'], value='[]', has_textbox=False, rank=i)
            parent.save()
            i += 1
            subchoice_ids = []
            for c in choice['subchoices']:
                c = Choice(question=question, body=c, value=c, has_textbox=False, rank=i)
                c.save()
                subchoice_ids.append(c.pk)
                i += 1
            parent.value = "[%s]" % (",".join([str(x) for x in subchoice_ids]),)
            parent.save()

        else:
            c = Choice(question=question, body=choice, value=choice, has_textbox=False, rank=i)
            c.save()
            i += 1

