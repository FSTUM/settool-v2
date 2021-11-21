from datetime import date, timedelta
from typing import Dict, List, Optional

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q, QuerySet, Sum
from django.forms import formset_factory
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from settool_common.models import get_semester, Semester

from ..forms import (
    FilterParticipantsForm,
    FilterRegisteredParticipantsForm,
    ParticipantAdminForm,
    ParticipantForm,
    SelectMailForm,
    SelectParticipantForm,
)
from ..models import FahrtMail, Participant, Transportation
from .tex_views import get_non_liability


@permission_required("fahrt.view_participants")
def list_registered(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    participants = semester.fahrt_participant.filter(status="registered").order_by(
        "-registration_time",
    )

    context = {
        "participants": participants,
    }
    return render(request, "fahrt/participants/list/list_registered.html", context)


@permission_required("fahrt.view_participants")
def list_waitinglist(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    participants = semester.fahrt_participant.filter(status="waitinglist").order_by(
        "-registration_time",
    )

    context = {
        "participants": participants,
    }
    return render(request, "fahrt/participants/list/list_waitinglist.html", context)


def get_possibly_filtered_participants(filterform, semester):
    participants = semester.fahrt_participant.filter(status="confirmed").order_by(
        "payment_deadline",
        "surname",
        "firstname",
    )
    if filterform.is_valid():
        non_liability = filterform.cleaned_data["non_liability"]
        if non_liability is not None:
            participants = participants.filter(non_liability__isnull=not non_liability)
        subject = filterform.cleaned_data["subject"]
        if subject is not None:
            participants = participants.filter(subject=subject)

        car = filterform.cleaned_data["car"]
        if car is not None:
            car_creators = semester.fahrt.transportation_set.filter(transport_type=Transportation.CAR).values("creator")
            participants = participants.filter(id__in=car_creators)

        paid = filterform.cleaned_data["paid"]
        if paid is not None:
            participants = participants.filter(paid__isnull=not paid)

        payment_deadline = filterform.cleaned_data["payment_deadline"]
        if payment_deadline:
            participants = participants.filter(
                payment_deadline__lt=timezone.now().date(),
            )
        elif payment_deadline is False:
            participants = participants.filter(
                payment_deadline__ge=timezone.now().date(),
            )

        mailinglist = filterform.cleaned_data["mailinglist"]
        if mailinglist is not None:
            participants = participants.filter(mailinglist=mailinglist)

        u18 = filterform.cleaned_data["u18"]
        if u18 is None:
            return participants
        participants_id = [p.id for p in participants if p.u18 == u18]
        participants.filter(id__in=participants_id)
    return participants


@permission_required("fahrt.view_participants")
def list_confirmed(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    filterform = FilterRegisteredParticipantsForm(request.POST or None, semester=semester)
    participants = get_possibly_filtered_participants(filterform, semester)

    u18s: int = sum(p.u18 for p in participants)
    allergies = participants.exclude(allergies="").count()

    number = participants.count()
    num_women = participants.filter(gender="female").count()
    proportion_of_women = int(num_women * 1.0 / number * 100) if number != 0 else 0

    cars = semester.fahrt.transportation_set.filter(transport_type=Transportation.CAR)

    context = {
        "filterform": filterform,
        "nutritions": get_nutritunal_information(participants, semester),
        "participants": participants,
        "number": number,
        "non_liability": participants.filter(non_liability__isnull=False).count(),
        "paid": participants.filter(paid__isnull=False).count(),
        "car_places": cars.aggregate(car_places=Sum("places"))["car_places"] or 0,
        "cars": cars.count(),
        "u18s": u18s,
        "allergies": allergies,
        "num_women": num_women,
        "proportion_of_women": proportion_of_women,
    }
    return render(request, "fahrt/participants/list/list_confirmed.html", context)


def get_nutritunal_information(
    participants: QuerySet[Participant],
    semester: Semester,
) -> List[Dict[str, object]]:
    nutritions = semester.fahrt_participant.filter(status="confirmed").values("nutrition").distinct()
    nutrition_choices = [choice["nutrition"] for choice in nutritions]
    return [
        {
            "name": choice,
            "count": str(participants.filter(nutrition=choice).count()),
            "allergies": participants.filter(nutrition=choice).exclude(allergies="").values("allergies"),
        }
        for choice in nutrition_choices
    ]


@permission_required("fahrt.view_participants")
def list_cancelled(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    participants = semester.fahrt_participant.filter(status="cancelled").order_by("surname")

    context = {
        "participants": participants,
    }
    return render(request, "fahrt/participants/list/list_cancelled.html", context)


@permission_required("fahrt.view_participants")
def view_participant(request: WSGIRequest, participant_pk: int) -> HttpResponse:
    participant = get_object_or_404(Participant, pk=participant_pk)
    log_entries = participant.logentry_set.order_by("time")

    form = SelectMailForm(request.POST or None)

    if form.is_valid():
        mail = form.cleaned_data["mail"]
        request.session["selected_participants"] = [participant.id]

        return redirect("fahrt:send_mail", mail.id)

    context = {
        "participant": participant,
        "log_entries": log_entries,
        "form": form,
    }
    return render(request, "fahrt/participants/view_participant_details.html", context)


@permission_required("fahrt.view_participants")
def edit_participant(request: WSGIRequest, participant_pk: int) -> HttpResponse:
    participant = get_object_or_404(Participant, pk=participant_pk)

    form = ParticipantAdminForm(
        request.POST or None,
        semester=participant.semester,
        instance=participant,
    )
    if form.is_valid():
        form.save()
        participant.log(request.user, "Participant edited")

        return redirect("fahrt:view_participant", participant.id)

    context = {
        "form": form,
        "participant": participant,
    }
    return render(request, "fahrt/participants/edit_participants.html", context)


@permission_required("fahrt.view_participants")
def del_participant(request: WSGIRequest, participant_pk: int) -> HttpResponse:
    participant = get_object_or_404(Participant, pk=participant_pk)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        participant.delete()

        return redirect("fahrt:main_index")

    context = {
        "form": form,
        "participant": participant,
    }
    return render(request, "fahrt/participants/del_participant.html", context)


@permission_required("fahrt.view_participants")
def toggle_mailinglist(request: WSGIRequest, participant_pk: int) -> HttpResponse:
    participant = get_object_or_404(Participant, pk=participant_pk)
    participant.toggle_mailinglist()
    participant.log(request.user, "Toggle mailinglist")

    return redirect("fahrt:view_participant", participant.id)


@permission_required("fahrt.view_participants")
def set_paid(request: WSGIRequest, participant_pk: int) -> HttpResponse:
    participant = get_object_or_404(Participant, pk=participant_pk)
    Participant.objects.filter(pk=participant_pk).update(
        paid=timezone.now().date(),
    )
    participant.log(request.user, "Set paid")

    return redirect("fahrt:view_participant", participant_pk)


@permission_required("fahrt.view_participants")
def set_nonliability(request: WSGIRequest, participant_pk: int) -> HttpResponse:
    participant = get_object_or_404(Participant, pk=participant_pk)
    Participant.objects.filter(pk=participant_pk).update(
        non_liability=timezone.now().date(),
    )
    participant.log(request.user, "Set non-liability")

    return redirect("fahrt:view_participant", participant_pk)


@permission_required("fahrt.view_participants")
def set_status_confirmed(request: WSGIRequest, participant_pk: int) -> HttpResponse:
    participant = get_object_or_404(Participant, pk=participant_pk)
    Participant.objects.filter(pk=participant_pk).update(
        status="confirmed",
    )
    participant.log(request.user, "Confirmed")

    return redirect("fahrt:view_participant", participant_pk)


@permission_required("fahrt.view_participants")
def set_status_waitinglist(request: WSGIRequest, participant_pk: int) -> HttpResponse:
    participant = get_object_or_404(Participant, pk=participant_pk)
    Participant.objects.filter(pk=participant_pk).update(
        status="waitinglist",
    )
    participant.log(request.user, "On waitinglist")

    return redirect("fahrt:view_participant", participant_pk)


@permission_required("fahrt.view_participants")
def set_payment_deadline(request: WSGIRequest, participant_pk: int, weeks: int) -> HttpResponse:
    weeks = int(weeks)  # save due to regex in urls.py
    if weeks not in [1, 2, 3]:
        raise Http404("Invalid number of weeks")

    participant = get_object_or_404(Participant, pk=participant_pk)
    Participant.objects.filter(pk=participant_pk).update(
        payment_deadline=date.today() + timedelta(days=weeks * 7),
    )
    participant.log(request.user, f"Set deadline {weeks} week")

    return redirect("fahrt:view_participant", participant_pk)


@permission_required("fahrt.view_participants")
def set_status_canceled(request: WSGIRequest, participant_pk: int) -> HttpResponse:
    participant = get_object_or_404(Participant, pk=participant_pk)
    Participant.objects.filter(pk=participant_pk).update(
        status="cancelled",
    )
    participant.log(request.user, "Cancelled")

    return redirect("fahrt:view_participant", participant_pk)


def signup(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    try:
        fahrt = semester.fahrt
    except ObjectDoesNotExist:
        return render(request, "fahrt/standalone/registration_closed.html")
    else:
        if not fahrt.registration_open:
            return render(request, "fahrt/standalone/registration_closed.html")

    form = ParticipantForm(request.POST or None, semester=semester)
    if form.is_valid():
        participant: Participant = form.save()
        participant.log(None, "Signed up")
        mail = fahrt.mail_registration
        if mail:
            non_liability: Optional[HttpResponse] = None
            try:
                non_liability = get_non_liability(request, participant.pk)
            except Http404:
                error: bool = True
            else:
                error = False
            if error or non_liability is None or not mail.send_mail_registration(participant, non_liability):
                messages.error(
                    request,
                    _(
                        "Could not send you the registration email. You are registered, but you did not receve all "
                        "nessesary documents. Please contact {mail} to get your non-liability form. ",
                    ).format(mail=FahrtMail.SET_FAHRT),
                )

        return redirect("fahrt:signup_success")

    context = {
        "semester": semester,
        "form": form,
    }
    return render(request, "fahrt/participants/signup/signup_external.html", context)


@permission_required("fahrt.view_participants")
def signup_internal(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))

    try:
        semester.fahrt
    except ObjectDoesNotExist:
        messages.error(request, _("Please setup the SETtings for the Fahrt"))
        return redirect("fahrt:settings")

    form = ParticipantForm(request.POST or None, semester=semester)
    if form.is_valid():
        participant: Participant = form.save()
        participant.log(request.user, "Signed up")
        mail = participant.semester.fahrt.mail_registration
        if mail:
            non_liability = get_non_liability(request, participant.pk)
            if not mail.send_mail_registration(participant, non_liability):
                messages.warning(
                    request,
                    _("Could not send the registration email. Make shure you configured the Registration-Mail."),
                )

        return redirect("fahrt:list_registered")

    context = {
        "semester": semester,
        "form": form,
        "management_view": True,
    }
    return render(request, "fahrt/participants/signup/signup_internal.html", context)


def signup_success(request: WSGIRequest) -> HttpResponse:
    return render(request, "fahrt/standalone/success.html")


@permission_required("fahrt.view_participants")
def filter_participants(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))

    participants = semester.fahrt_participant.order_by("surname")

    filterform = FilterParticipantsForm(request.POST or None)
    if filterform.is_valid():
        set_request_session_filtered_participants(filterform, participants, request, semester)
        return redirect("fahrt:filtered_participants")

    context = {
        "participants": participants,
        "filterform": filterform,
    }
    return render(request, "fahrt/maintinance/mail/filter_participants_send_mail.html", context)


def set_request_session_filtered_participants(filterform, participants, request, semester):
    search = filterform.cleaned_data["search"]
    if search:
        participants = participants.filter(
            Q(firstname__icontains=search) | Q(surname__icontains=search) | Q(comment__icontains=search),
        )

    non_liability = filterform.cleaned_data["non_liability"]
    if non_liability:
        participants = participants.filter(non_liability__isnull=False)
    elif non_liability is False:
        participants = participants.filter(non_liability__isnull=True)

    car = filterform.cleaned_data["car"]
    if car is not None:
        car_creators = semester.fahrt.transportation_set.filter(transport_type=Transportation.CAR).values("creator")
        participants = participants.filter(id__in=car_creators)

    paid = filterform.cleaned_data["paid"]
    if paid:
        participants = participants.filter(paid__isnull=False)
    elif paid is False:
        participants = participants.filter(paid__isnull=True)

    payment_deadline = filterform.cleaned_data["payment_deadline"]
    if payment_deadline:
        participants = participants.filter(
            payment_deadline__lt=timezone.now().date(),
        )
    elif payment_deadline is False:
        participants = participants.filter(
            payment_deadline__ge=timezone.now().date(),
        )

    mailinglist = filterform.cleaned_data["mailinglist"]
    if mailinglist is not None:
        participants = participants.filter(mailinglist=mailinglist)

    status = filterform.cleaned_data["status"]
    if status:
        participants = participants.filter(status=status)

    u18 = filterform.cleaned_data["u18"]
    if u18:
        participants = [p for p in participants if p.u18]
    elif u18 is False:
        participants = [p for p in participants if not p.u18]

    filtered_participants = [p.id for p in participants]
    request.session["filtered_participants"] = filtered_participants


@permission_required("fahrt.view_participants")
def filtered_list(request: WSGIRequest) -> HttpResponse:
    filtered_participants = request.session["filtered_participants"]
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    participants = semester.fahrt_participant.filter(
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
        return redirect("fahrt:send_mail", mail.id)

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
    return render(request, "fahrt/maintinance/mail/list_filtered_participants_send_mail.html", context)
