from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import permission_required

from . models import Participant
from .forms import ParticipantForm
from settool_common.models import get_semester, Semester


# TODO: remove permission
@permission_required('fahrt.view_participants')
def signup(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)

    form = ParticipantForm(request.POST or None, semester=semester)
    if form.is_valid():
        participant = form.save()

        return redirect('signup_success', participant.id)

    context = {'semester': semester,
               'form': form}
    return render(request, 'fahrt/add.html', context)


# TODO: remove permission
@permission_required('fahrt.view_participants')
def signup_success(request, participant_pk):
    participant = get_object_or_404(Participant, pk=participant_pk)
    context = {'participant': participant}
    return render(request, 'fahrt/success.html', context)

