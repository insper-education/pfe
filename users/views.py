from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import generic

from .forms import PFEUserCreationForm

class SignUp(generic.CreateView):
    form_class = PFEUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'signup.html'
