from django import forms
from django.contrib.auth.decorators import permission_required
from django.db.models import Q
from django.forms import formset_factory
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from settool_common.models import get_semester, Semester
from .forms import ParticipantForm, TourForm, FilterParticipantsForm, \
    SelectMailForm, SelectParticipantForm, MailForm
from .models import Tour, Participant, Mail


@permission_required('guidedtours.view_participants')
def index(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    tours = semester.tour_set.all()

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


@permission_required('guidedtours.view_participants')
def add(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)

    form = TourForm(request.POST or None,
                    semester=semester)

    if form.is_valid():
        form.save()

        return redirect('tours_list')

    context = {
        'form': form,
    }
    return render(request, 'guidedtours/add.html', context)


@permission_required('guidedtours.view_participants')
def edit(request, tour_pk):
    tour = get_object_or_404(Tour, pk=tour_pk)

    form = TourForm(request.POST or None,
                    semester=tour.semester,
                    instance=tour)
    if form.is_valid():
        form.save()

        return redirect('tours_view', tour.id)

    context = {
        'form': form,
        'tour': tour,
    }
    return render(request, 'guidedtours/edit.html', context)


@permission_required('guidedtours.view_participants')
def delete(request, tour_pk):
    tour = get_object_or_404(Tour, pk=tour_pk)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        tour.delete()

        return redirect('tours_list')

    context = {
        'form': form,
        'tour': tour,
    }
    return render(request, 'guidedtours/del.html', context)


@permission_required('guidedtours.view_participants')
def filter_participants(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    participants = Participant.objects.filter(
        tour__semester=semester.id).order_by('surname')

    filterform = FilterParticipantsForm(request.POST or None,
                                        semester=semester)

    if filterform.is_valid():
        search = filterform.cleaned_data['search']
        on_the_tour = filterform.cleaned_data['on_the_tour']
        tour = filterform.cleaned_data['tour']

        if search:
            participants = participants.filter(
                Q(firstname__icontains=search) |
                Q(surname__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search) |
                Q(tour__name__icontains=search) |
                Q(tour__description__icontains=search)
            )

        if tour is not None:
            participants = participants.filter(tour=tour)

        if on_the_tour:
            participants = [p for p in participants if p.on_the_tour]
        elif on_the_tour is False:
            participants = [p for p in participants if not p.on_the_tour]

        filtered_participants = [p.id for p in participants]
        request.session['filtered_participants'] = filtered_participants
        return redirect('tours_filteredparticipants')

    context = {
        'participants': participants,
        'filterform': filterform,
    }
    return render(request, 'guidedtours/filter.html', context)


@permission_required('guidedtours.view_participants')
def filtered_list(request):
    filtered_participants = request.session['filtered_participants']
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    participants = Participant.objects.filter(
        id__in=filtered_participants).order_by("surname")

    form = SelectMailForm(request.POST or None, semester=semester)
    select_participant_form_set = formset_factory(SelectParticipantForm,
                                                  extra=0)
    participantforms = select_participant_form_set(request.POST or None,
                                                   initial=[{'id': p.id, 'selected': True} for p in participants],
                                                   )

    if form.is_valid() and participantforms.is_valid():
        mail = form.cleaned_data['mail']

        selected_participants = []
        for i, participant in enumerate(participantforms):
            try:
                participant_id = participant.cleaned_data['id']
            except KeyError:
                continue
            try:
                selected = participant.cleaned_data['selected']
            except KeyError:
                selected = False
            if selected:
                selected_participants.append(participant_id)

        request.session['selected_participants'] = selected_participants
        return redirect('tours_sendmail', mail.id)

    participants_and_select = []
    for p in participants:
        for s in participantforms:
            if s.initial['id'] == p.id:
                participants_and_select.append((p, s))
                break

    context = {
        'participants': participants_and_select,
        'form': form,
        'participantforms': participantforms,
    }
    return render(request, 'guidedtours/filtered_list.html', context)


@permission_required('guidedtours.view_participants')
def index_mails(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    mails = semester.tours_mail_set.all()

    context = {'mails': mails}
    return render(request, 'guidedtours/index_mails.html', context)


@permission_required('guidedtours.view_participants')
def add_mail(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)

    form = MailForm(request.POST or None, semester=semester)
    if form.is_valid():
        form.save()

        return redirect('tours_listmails')

    context = {'form': form}
    return render(request, 'guidedtours/add_mail.html', context)


@permission_required('guidedtours.view_participants')
def edit_mail(request, mail_pk):
    mail = get_object_or_404(Mail, pk=mail_pk)

    form = MailForm(request.POST or None, semester=mail.semester,
                    instance=mail)
    if form.is_valid():
        form.save()

        return redirect('tours_listmails')

    context = {
        'form': form,
        'mail': mail,
    }
    return render(request, 'guidedtours/edit_mail.html', context)


@permission_required('guidedtours.view_participants')
def delete_mail(request, mail_pk):
    mail = get_object_or_404(Mail, pk=mail_pk)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        mail.delete()

        return redirect('tours_listmails')

    context = {'mail': mail,
               'form': form}
    return render(request, 'guidedtours/del_mail.html', context)


@permission_required('guidedtours.view_participants')
def send_mail(request, mail_pk):
    mail = get_object_or_404(Mail, pk=mail_pk)
    selected_participants = request.session['selected_participants']
    participants = Participant.objects.filter(
        id__in=selected_participants).order_by("surname")

    subject, text, from_email = mail.get_mail()

    form = forms.Form(request.POST or None)
    if form.is_valid():
        for p in participants:
            mail.send_mail(p)
        return redirect('tours_filter')

    context = {
        'participants': participants,
        'subject': subject,
        'text': text,
        'from_email': from_email,
        'form': form,
    }

    return render(request, 'guidedtours/send_mail.html', context)


def signup(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    tours = semester.tour_set.filter(open_registration__lt=timezone.now(),
                                     close_registration__gt=timezone.now()).order_by('date')

    if not tours:
        context = {'semester': semester}
        return render(request, 'guidedtours/signup_notour.html', context)

    form = ParticipantForm(request.POST or None, tours=tours)
    if form.is_valid():
        form.save()
        return redirect('tours_signup_success')

    context = {
        'semester': semester,
        'form': form,
        'tours': tours,
    }
    return render(request, 'guidedtours/signup.html', context)


def signup_success(request):
    return render(request, 'guidedtours/success.html', {})


@permission_required('guidedtours.view_participants')
def signup_internal(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    tours = semester.tour_set.order_by('date')

    if not tours:
        return redirect('tours_add')

    form = ParticipantForm(request.POST or None, tours=tours)
    if form.is_valid():
        participant = form.save()

        return redirect('tours_view', participant.tour.id)

    context = {'semester': semester,
               'form': form}
    return render(request, 'guidedtours/signup_internal.html', context)
