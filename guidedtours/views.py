import time
from typing import Any, Dict

from django import forms
from django.contrib.auth.decorators import permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q, QuerySet
from django.db.models.aggregates import Count
from django.forms import formset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.datetime_safe import date

from settool_common import utils
from settool_common.models import get_semester, Semester

from .forms import FilterParticipantsForm, MailForm, ParticipantForm, SelectMailForm, SelectParticipantForm, TourForm
from .models import Participant, Tour, TourMail


@permission_required("guidedtours.view_participants")
def list_tours(request: WSGIRequest) -> HttpResponse:
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    tours = semester.tour_set.all()

    context = {"tours": tours}
    return render(request, "guidedtours/tours/list_tours.html", context)


@permission_required("guidedtours.view_participants")
def dashboard(request: WSGIRequest) -> HttpResponse:
    tours = (
        Tour.objects.filter(Q(semester=get_semester(request)) & Q(date__gte=date.today()))
        .values("capacity", "name", "date")
        .annotate(registered=Count("participant"))
        .order_by("date")
    )

    context = {
        "tour_labels": [f"{tour['name']} {tour['date'].strftime('%d.%m %H')}Uhr" for tour in tours],
        "tour_registrations": [tour["registered"] for tour in tours],
        "tour_capacity": [tour["capacity"] for tour in tours],
    }
    return render(request, "guidedtours/tour_dashboard.html", context)


@permission_required("guidedtours.view_participants")
def view(request: WSGIRequest, tour_pk: int) -> HttpResponse:
    tour = get_object_or_404(Tour, pk=tour_pk)
    participants = tour.participant_set.order_by("time")
    waitinglist = participants[tour.capacity :]
    participants = participants[: tour.capacity]

    context = {
        "tour": tour,
        "participants": participants,
        "waitinglist": waitinglist,
    }
    return render(request, "guidedtours/participants/list_tour-participants.html", context)


@permission_required("guidedtours.view_participants")
def add(request: WSGIRequest) -> HttpResponse:
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)

    form = TourForm(
        request.POST or None,
        semester=semester,
    )

    if form.is_valid():
        form.save()

        return redirect("tours_list_tours")

    context = {
        "form": form,
    }
    return render(request, "guidedtours/tours/add_tour.html", context)


@permission_required("guidedtours.view_participants")
def edit(request: WSGIRequest, tour_pk: int) -> HttpResponse:
    tour = get_object_or_404(Tour, pk=tour_pk)

    form = TourForm(
        request.POST or None,
        semester=tour.semester,
        instance=tour,
    )
    if form.is_valid():
        form.save()

        return redirect("tours_view", tour.id)

    context = {
        "form": form,
        "tour": tour,
    }
    return render(request, "guidedtours/tours/edit_tour.html", context)


@permission_required("guidedtours.view_participants")
def delete(request: WSGIRequest, tour_pk: int) -> HttpResponse:
    tour = get_object_or_404(Tour, pk=tour_pk)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        tour.delete()

        return redirect("tours_list_tours")

    context = {
        "form": form,
        "tour": tour,
    }
    return render(request, "guidedtours/tours/del_tour.html", context)


@permission_required("guidedtours.view_participants")
def filter_participants(request: WSGIRequest) -> HttpResponse:
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    participants: QuerySet[Participant] = Participant.objects.filter(
        tour__semester=semester.id,
    ).order_by("surname")

    filterform = FilterParticipantsForm(
        request.POST or None,
        semester=semester,
    )

    if filterform.is_valid():
        search = filterform.cleaned_data["search"]
        on_the_tour = filterform.cleaned_data["on_the_tour"]
        tour = filterform.cleaned_data["tour"]

        if search:
            participants = participants.filter(
                Q(firstname__icontains=search)
                | Q(surname__icontains=search)
                | Q(email__icontains=search)
                | Q(phone__icontains=search)
                | Q(tour__name__icontains=search)
                | Q(tour__description__icontains=search),
            )

        if tour is not None:
            participants = participants.filter(tour=tour)
        filtered_participants = [p.id for p in participants]
        if on_the_tour:
            filtered_participants = [p.id for p in participants if p.on_the_tour]
        elif on_the_tour is False:
            filtered_participants = [p.id for p in participants if not p.on_the_tour]

        request.session["filtered_participants"] = filtered_participants
        return redirect("tours_filteredparticipants")

    context = {
        "participants": participants,
        "filterform": filterform,
    }
    return render(request, "guidedtours/participants/filter_participants.html", context)


@permission_required("guidedtours.view_participants")
def filtered_list(request: WSGIRequest) -> HttpResponse:
    filtered_participants = request.session["filtered_participants"]
    participants = Participant.objects.filter(
        id__in=filtered_participants,
    ).order_by("surname")

    form = SelectMailForm(request.POST or None)
    select_participant_form_set = formset_factory(
        SelectParticipantForm,
        extra=0,
    )
    participantforms = select_participant_form_set(
        request.POST or None,
        initial=[{"id": p.id, "selected": True} for p in participants],
    )

    if form.is_valid() and participantforms.is_valid():
        mail = form.cleaned_data["mail"]

        selected_participants = []
        for participant in participantforms:
            try:
                participant_id = participant.cleaned_data["id"]
            except KeyError:
                continue
            try:
                selected = participant.cleaned_data["selected"]
            except KeyError:
                selected = False
            if selected:
                selected_participants.append(participant_id)

        request.session["selected_participants"] = selected_participants
        return redirect("tours_sendmail", mail.id)

    participants_and_select = []
    for participant in participants:
        for participant_form in participantforms:
            if participant_form.initial["id"] == participant.id:
                participants_and_select.append((participant, participant_form))
                break

    context = {
        "participants": participants_and_select,
        "form": form,
        "participantforms": participantforms,
    }
    return render(request, "guidedtours/participants/filtered_participants.html", context)


@permission_required("guidedtours.view_participants")
def index_mails(request: WSGIRequest) -> HttpResponse:
    context = {"mails": TourMail.objects.all()}
    return render(request, "guidedtours/mail/index_mails.html", context)


@permission_required("guidedtours.view_participants")
def add_mail(request: WSGIRequest) -> HttpResponse:
    form = MailForm(request.POST or None)
    if form.is_valid():
        form.save()

        return redirect("tours_listmails")

    context = {"form": form}
    return render(request, "guidedtours/mail/add_mail.html", context)


@permission_required("guidedtours.view_participants")
def edit_mail(request: WSGIRequest, mail_pk: int) -> HttpResponse:
    mail = get_object_or_404(TourMail, pk=mail_pk)

    form = MailForm(request.POST or None, instance=mail)
    if form.is_valid():
        form.save()

        return redirect("tours_listmails")

    context = {
        "form": form,
        "mail": mail,
    }
    return render(request, "guidedtours/mail/edit_mail.html", context)


@permission_required("guidedtours.view_participants")
def delete_mail(request: WSGIRequest, mail_pk: int) -> HttpResponse:
    mail = get_object_or_404(TourMail, pk=mail_pk)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        mail.delete()

        return redirect("tours_listmails")

    context = {
        "mail": mail,
        "form": form,
    }
    return render(request, "guidedtours/mail/del_mail.html", context)


@permission_required("guidedtours.view_participants")
def send_mail(request: WSGIRequest, mail_pk: int) -> HttpResponse:
    mail = get_object_or_404(TourMail, pk=mail_pk)
    selected_participants = request.session["selected_participants"]
    participants = Participant.objects.filter(
        id__in=selected_participants,
    ).order_by("surname")

    subject, text, from_email = mail.get_mail_participant()

    form = forms.Form(request.POST or None)
    if form.is_valid():
        for participant in participants:
            mail.send_mail_participant(participant)
        return redirect("tours_filter")

    context = {
        "participants": participants,
        "subject": subject,
        "text": text,
        "from_email": from_email,
        "form": form,
    }

    return render(request, "guidedtours/mail/send_mail.html", context)


def signup(request: WSGIRequest) -> HttpResponse:
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    tours = semester.tour_set.filter(
        open_registration__lt=timezone.now(),
        close_registration__gt=timezone.now(),
    ).order_by("date")

    if not tours:
        context: Dict[str, Any] = {"semester": semester}
        return render(request, "guidedtours/signup/signup_notour.html", context)

    form = ParticipantForm(request.POST or None, tours=tours)
    if form.is_valid():
        form.save()
        return redirect("tours_signup_success")

    context = {
        "semester": semester,
        "form": form,
        "tours": tours,
    }
    return render(request, "guidedtours/signup/signup.html", context)


def signup_success(request: WSGIRequest) -> HttpResponse:
    return render(request, "guidedtours/signup/success.html")


@permission_required("guidedtours.view_participants")
def signup_internal(request: WSGIRequest) -> HttpResponse:
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    tours = semester.tour_set.order_by("date")

    if not tours:
        return redirect("tours_add")

    form = ParticipantForm(request.POST or None, tours=tours)
    if form.is_valid():
        participant = form.save()

        return redirect("tours_view", participant.tour.id)

    context = {
        "semester": semester,
        "form": form,
    }
    return render(request, "guidedtours/signup/signup_internal.html", context)


@permission_required("guidedtours.view_participants")
def export(request: WSGIRequest, file_format: str, tour_pk: int) -> HttpResponse:
    tour = get_object_or_404(Tour, pk=tour_pk)
    participants = tour.participant_set.order_by("time")
    confirmed_participants = participants[: tour.capacity]
    filename = f"participants_{tour.name}_{tour.date}_{time.strftime('%Y%m%d-%H%M')}"
    context = {"participants": confirmed_participants, "tour": tour}
    if file_format == "csv":
        return utils.download_csv(
            ["surname", "firstname", "time", "email", "phone", "subject"],
            f"{filename}.csv",
            confirmed_participants,
        )
    return utils.download_pdf("guidedtours/tex/tour.tex", f"{filename}.pdf", context)
