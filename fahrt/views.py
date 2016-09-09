from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import permission_required
from django import forms
from django.utils import timezone
from django.db.models import Sum, F

from . models import Participant
from .forms import ParticipantForm, ParticipantAdminForm
from settool_common.models import get_semester, Semester


@permission_required('fahrt.view_participants')
def list_registered(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    participants = semester.fahrt_participant.filter(status='registered'
        ).order_by('surname')

    context = {
        'participants': participants,
    }
    return render(request, 'fahrt/list_registered.html', context)


@permission_required('fahrt.view_participants')
def list_confirmed(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    participants = semester.fahrt_participant.filter(status='confirmed'
        ).order_by('surname')

    u18s = [p for p in participants if p.u18]

    context = {
        'participants': participants,
        'number': participants.count(),
        'non_liability': participants.filter(
            non_liability__isnull=False).count(),
        'paid': participants.filter(paid__isnull=False).count(),
        'places': participants.filter(car=True).aggregate(
            places=Sum('car_places')),
        'cars': participants.filter(car=True).count(),
        'u18s': len(u18s),
    }
    return render(request, 'fahrt/list_confirmed.html', context)


@permission_required('fahrt.view_participants')
def list_cancelled(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    participants = semester.fahrt_participant.filter(status='cancelled'
        ).order_by('surname')

    context = {
        'participants': participants,
    }
    return render(request, 'fahrt/list_cancelled.html', context)


@permission_required('fahrt.view_participants')
def view(request, participant_pk):
    participant = get_object_or_404(Participant, pk=participant_pk)

    context = {'participant': participant}
    return render(request, 'fahrt/view.html', context)


@permission_required('fahrt.view_participants')
def edit(request, participant_pk):
    participant = get_object_or_404(Participant, pk=participant_pk)

    form = ParticipantAdminForm(request.POST or None,
            semester=participant.semester,
            instance=participant)
    if form.is_valid():
        form.save()

        return redirect('fahrt_viewparticipant', participant.id)

    context = {
        'form': form,
        'participant': participant,
    }
    return render(request, 'fahrt/edit.html', context)


@permission_required('fahrt.view_participants')
def delete(request, participant_pk):
    participant = get_object_or_404(Participant, pk=participant_pk)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        participant.delete()

        return redirect('index')

    context = {
        'form': form,
        'participant': participant,
    }
    return render(request, 'fahrt/del.html', context)


@permission_required('fahrt.view_participants')
def toggle_mailinglist(request, participant_pk):
    participant = get_object_or_404(Participant, pk=participant_pk)
    Participant.objects.filter(pk=participant_pk).update(
        mailinglist=(not participant.mailinglist),
    )
    participant.toggle_mailinglist()

    return redirect('fahrt_viewparticipant', participant.id)


@permission_required('fahrt.view_participants')
def set_paid(request, participant_pk):
    Participant.objects.filter(pk=participant_pk).update(
        paid=timezone.now().date(),
    )

    return redirect('fahrt_viewparticipant', participant_pk)


@permission_required('fahrt.view_participants')
def set_nonliability(request, participant_pk):
    Participant.objects.filter(pk=participant_pk).update(
        non_liability=timezone.now().date(),
    )

    return redirect('fahrt_viewparticipant', participant_pk)


@permission_required('fahrt.view_participants')
def confirm(request, participant_pk):
    Participant.objects.filter(pk=participant_pk).update(
        status="confirmed",
    )

    return redirect('fahrt_viewparticipant', participant_pk)


@permission_required('fahrt.view_participants')
def cancel(request, participant_pk):
    Participant.objects.filter(pk=participant_pk).update(
        status="cancelled",
    )

    return redirect('fahrt_viewparticipant', participant_pk)


# TODO: remove permission
@permission_required('fahrt.view_participants')
def signup(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)

    form = ParticipantForm(request.POST or None, semester=semester)
    if form.is_valid():
        participant = form.save()

        return redirect('fahrt_signup_success', participant.id)

    context = {'semester': semester,
               'form': form}
    return render(request, 'fahrt/add.html', context)


# TODO: remove permission
@permission_required('fahrt.view_participants')
def signup_success(request, participant_pk):
    participant = get_object_or_404(Participant, pk=participant_pk)
    context = {'participant': participant}
    return render(request, 'fahrt/success.html', context)

