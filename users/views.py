from django.shortcuts import render
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.urls import reverse_lazy
from django.views import generic
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.db import transaction

from .forms import PFEUserCreationForm, PFEUserForm, AlunoForm
from .models import PFEUser, Aluno, Professor, Funcionario

class SignUp(generic.CreateView):
    form_class = PFEUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'signup.html'

class Usuario(generic.DetailView):
    model = Aluno

def show_profile(request, pk):
    user = PFEUser.objects.get(pk=pk)
    user.profile.bio = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit...'
    user.profile.location = 'Sao Paulo'
    user.save()
    return HttpResponse("Tudo certo!")

@login_required
@transaction.atomic
def update_profile(request):
    if request.method == 'POST':
        pfeuser_form = PFEUserForm(request.POST, instance=request.user)
        aluno_form = AlunoForm(request.POST, instance=request.user.profile)
        if pfeuser_form.is_valid() and aluno_form.is_valid():
            pfeuser_form.save()
            aluno_form.save()
            messages.success(request, _('Your profile was successfully updated!'))
            return redirect('signup')
        else:
            messages.error(request, _('Please correct the error below.'))
    else:
        pfeuser_form = PFEUserForm(instance=request.user)
        aluno_form = AlunoForm(instance=request.user.profile)
    return render(request, 'users/profile.html', {
        'pfeuser_form': pfeuser_form,
        'aluno_form': aluno_form
    })