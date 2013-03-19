from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.core.urlresolvers import reverse
from .surveys.models import Survey, Question
from .surveys.forms import SurveyForm

def home(request):
    return render(request, "home.html", {

    })
