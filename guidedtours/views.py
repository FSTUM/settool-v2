from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import permission_required

from .models import Tour, Participant
from .forms import ParticipantForm
from settool_common.settings import SEMESTER_SESSION_KEY
from settool_common.models import current_semester, Semester

@permission_required('guidedtours.view_participants')
def index(request):
    tours = Tour.objects.order_by('date')

    context = {'tours': tours}
    return render(request, 'guidedtours/index.html', context)


@permission_required('guidedtours.view_participants')
def view(request, tour_pk):
    tour = get_object_or_404(Tour, pk=tour_pk)
    participants = tour.participant_set.order_by('time')
    waitinglist = participants[tour.capacity:]
    participants = participants[:tour.capacity]

    context = {'tour': tour,
               'participants': participants,
               'waitinglist': waitinglist}
    return render(request, 'guidedtours/view.html', context)


def signup(request):
    if not hasattr(request.session, SEMESTER_SESSION_KEY):
        request.session[SEMESTER_SESSION_KEY] = current_semester().pk
    semester = get_object_or_404(Semester,
        pk=request.session[SEMESTER_SESSION_KEY])
    tours = semester.tour_set.all()

    if not tours:
        context = {'semester': semester}
        return render(request, 'guidedtours/add_notour.html', context)

    form = ParticipantForm(request.POST or None, tours=tours)
    if form.is_valid():
        participant = form.save()

        return redirect('signup_success', participant.id)

    context = {'semester': semester,
               'form': form}
    return render(request, 'guidedtours/add.html', context)


def signup_success(request, participant_pk):
    participant = get_object_or_404(Participant, pk=participant_pk)
    context = {'participant': participant}
    return render(request, 'guidedtours/success.html', context)
