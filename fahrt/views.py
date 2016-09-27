from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import permission_required
from django import forms
from django.utils import timezone
from django.db.models import Sum, F, Q
from django.forms import formset_factory
from django.core.exceptions import ObjectDoesNotExist

from . models import Participant, Mail, Fahrt, LogEntry
from .forms import ParticipantForm, ParticipantAdminForm, MailForm, \
    SelectParticipantForm, SelectMailForm, FilterParticipantsForm, FahrtForm
from settool_common.models import get_semester, Semester


@permission_required('fahrt.view_participants')
def index(request):
    return render(request, 'fahrt/base.html', {})


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

    number = participants.count()
    num_women = participants.filter(gender="female").count()
    if number == 0:
        proportion_of_women = 0
    else:
        proportion_of_women = int(num_women / number * 100)

    places = participants.filter(car=True).aggregate(places=Sum('car_places'))
    places = places['places'] or 0

    context = {
        'participants': participants,
        'number': number,
        'non_liability': participants.filter(
            non_liability__isnull=False).count(),
        'paid': participants.filter(paid__isnull=False).count(),
        'places': places,
        'cars': participants.filter(car=True).count(),
        'u18s': len(u18s),
        'num_women': num_women,
        'proportion_of_women': proportion_of_women,
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
    log_entries = participant.logentry_set.order_by('time')
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)

    form = SelectMailForm(request.POST or None, semester=semester)

    if form.is_valid():
        mail = form.cleaned_data['mail']
        request.session['selected_participants'] = [participant.id]

        return redirect('fahrt_sendmail', mail.id)

    context = {
        'participant': participant,
        'log_entries': log_entries,
        'form': form,
    }
    return render(request, 'fahrt/view.html', context)


@permission_required('fahrt.view_participants')
def edit(request, participant_pk):
    participant = get_object_or_404(Participant, pk=participant_pk)

    form = ParticipantAdminForm(request.POST or None,
            semester=participant.semester,
            instance=participant)
    if form.is_valid():
        form.save()
        participant.log(request.user, "Participant edited")

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

        return redirect('fahrt_index')

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
    participant = get_object_or_404(Participant, pk=participant_pk)
    participant.toggle_mailinglist()
    participant.log(request.user, "Toggle mailinglist")

    return redirect('fahrt_viewparticipant', participant.id)


@permission_required('fahrt.view_participants')
def set_paid(request, participant_pk):
    participant = get_object_or_404(Participant, pk=participant_pk)
    Participant.objects.filter(pk=participant_pk).update(
        paid=timezone.now().date(),
    )
    participant.log(request.user, "Set paid")

    return redirect('fahrt_viewparticipant', participant_pk)


@permission_required('fahrt.view_participants')
def set_nonliability(request, participant_pk):
    participant = get_object_or_404(Participant, pk=participant_pk)
    Participant.objects.filter(pk=participant_pk).update(
        non_liability=timezone.now().date(),
    )
    participant.log(request.user, "Set non-liability")

    return redirect('fahrt_viewparticipant', participant_pk)


@permission_required('fahrt.view_participants')
def confirm(request, participant_pk):
    participant = get_object_or_404(Participant, pk=participant_pk)
    Participant.objects.filter(pk=participant_pk).update(
        status="confirmed",
    )
    participant.log(request.user, "Confirmed")

    return redirect('fahrt_viewparticipant', participant_pk)


@permission_required('fahrt.view_participants')
def cancel(request, participant_pk):
    participant = get_object_or_404(Participant, pk=participant_pk)
    Participant.objects.filter(pk=participant_pk).update(
        status="cancelled",
    )
    participant.log(request.user, "Cancelled")

    return redirect('fahrt_viewparticipant', participant_pk)


def signup(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)

    try:
        fahrt = semester.fahrt
    except ObjectDoesNotExist:
        registration_open = False
    else:
        registration_open = fahrt.registration_open

    if not registration_open:
        return render(request, 'fahrt/registration_closed.html', {})

    form = ParticipantForm(request.POST or None, semester=semester)
    if form.is_valid():
        participant = form.save()
        participant.log(None, "Signed up")

        return redirect('fahrt_signup_success')

    context = {'semester': semester,
               'form': form}
    return render(request, 'fahrt/signup.html', context)


@permission_required('fahrt.view_participants')
def signup_internal(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)

    form = ParticipantForm(request.POST or None, semester=semester)
    if form.is_valid():
        participant = form.save()
        participant.log(request.user, "Signed up")

        return redirect('fahrt_list_registered')

    context = {'semester': semester,
               'form': form}
    return render(request, 'fahrt/add.html', context)


def signup_success(request):
    return render(request, 'fahrt/success.html', {})


@permission_required('fahrt.view_participants')
def filter(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    participants = semester.fahrt_participant.order_by('surname')

    filterform = FilterParticipantsForm(request.POST or None)

    if filterform.is_valid():
        search = filterform.cleaned_data['search']
        non_liability = filterform.cleaned_data['non_liability']
        u18 = filterform.cleaned_data['u18']
        car = filterform.cleaned_data['car']
        paid = filterform.cleaned_data['paid']
        payment_deadline = filterform.cleaned_data['payment_deadline']
        mailinglist = filterform.cleaned_data['mailinglist']
        status = filterform.cleaned_data['status']

        if search:
            participants = participants.filter(
                Q(firstname__icontains=search) |
                Q(surname__icontains=search) |
                Q(comment__icontains=search)
            )

        if non_liability:
            participants = participants.filter(non_liability__isnull=False)
        elif non_liability is False:
            participants = participants.filter(non_liability__isnull=True)

        if car is not None:
            participants = participants.filter(car=car)

        if paid:
            participants = participants.filter(paid__isnull=False)
        elif paid is False:
            participants = participants.filter(paid__isnull=True)

        if payment_deadline:
            participants = participants.filter(
                payment_deadline__lt=timezone.now().date())
        elif payment_deadline is False:
            participants = participants.filter(
                payment_deadline__ge=timezone.now().date())

        if mailinglist is not None:
            participants = participants.filter(mailinglist=mailinglist)

        if status:
            participants = participants.filter(status=status)

        if u18:
            participants = [p for p in participants if p.u18]
        elif u18 is False:
            participants = [p for p in participants if not p.u18]

        filtered_participants = [p.id for p in participants]
        request.session['filtered_participants'] = filtered_participants
        return redirect('fahrt_filteredparticipants')

    context = {
        'participants': participants,
        'filterform': filterform,
    }
    return render(request, 'fahrt/filter.html', context)


@permission_required('fahrt.view_participants')
def filtered_list(request):
    filtered_participants = request.session['filtered_participants']
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    participants = semester.fahrt_participant.filter(
        id__in=filtered_participants).order_by("surname")

    form = SelectMailForm(request.POST or None, semester=semester)
    SelectParticipantFormSet = formset_factory(SelectParticipantForm,
        extra=0)
    participantforms = SelectParticipantFormSet(request.POST or None,
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
        return redirect('fahrt_sendmail', mail.id)

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
    return render(request, 'fahrt/filtered_list.html', context)


@permission_required('fahrt.view_participants')
def index_mails(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    mails = semester.fahrt_mail_set.all()

    context = {'mails': mails}
    return render(request, 'fahrt/index_mails.html', context)


@permission_required('fahrt.view_participants')
def add_mail(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)

    form = MailForm(request.POST or None, semester=semester)
    if form.is_valid():
        form.save()

        return redirect('fahrt_listmails')

    context = {'form': form}
    return render(request, 'fahrt/add_mail.html', context)


@permission_required('fahrt.view_participants')
def edit_mail(request, mail_pk):
    mail = get_object_or_404(Mail, pk=mail_pk)

    form = MailForm(request.POST or None, semester=mail.semester,
            instance=mail)
    if form.is_valid():
        form.save()

        return redirect('fahrt_listmails')

    context = {
        'form': form,
        'mail': mail,
    }
    return render(request, 'fahrt/edit_mail.html', context)


@permission_required('fahrt.view_participants')
def delete_mail(request, mail_pk):
    mail = get_object_or_404(Mail, pk=mail_pk)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        mail.delete()

        return redirect('fahrt_listmails')

    context = {'mail': mail,
               'form': form}
    return render(request, 'fahrt/del_mail.html', context)


@permission_required('fahrt.view_participants')
def send_mail(request, mail_pk):
    mail = get_object_or_404(Mail, pk=mail_pk)
    selected_participants = request.session['selected_participants']
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    participants = semester.fahrt_participant.filter(
        id__in=selected_participants).order_by("surname")

    subject, text, from_email = mail.get_mail(request)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        for p in participants:
            mail.send_mail(request, p)
            p.log(request.user, "Mail '{0}' sent".format(mail))
        return redirect('fahrt_filter')

    context = {
        'participants': participants,
        'subject': subject,
        'text': text,
        'from_email': from_email,
        'form': form,
    }

    return render(request, 'fahrt/send_mail.html', context)


@permission_required('fahrt.view_participants')
def change_date(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)

    try:
        fahrt = semester.fahrt
    except ObjectDoesNotExist:
        fahrt = Fahrt.objects.create(
            semester=semester,
            date=timezone.now().date(),
            open_registration=timezone.now(),
            close_registration=timezone.now(),
        )

    form = FahrtForm(request.POST or None, semester=semester,
            instance=fahrt)
    if form.is_valid():
        form.save()

        return redirect('fahrt_date')

    context = {
        'form': form,
    }
    return render(request, 'fahrt/change_date.html', context)
