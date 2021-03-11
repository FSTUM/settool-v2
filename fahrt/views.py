import time
from datetime import date, timedelta
from io import TextIOWrapper
from typing import Dict, List, Optional

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.uploadedfile import UploadedFile
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Count, Q, QuerySet, Sum
from django.forms import formset_factory
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from settool_common import utils
from settool_common.models import get_semester, Semester, Subject

from .forms import (
    CSVFileUploadForm,
    FahrtForm,
    FilterParticipantsForm,
    FilterRegisteredParticipantsForm,
    MailForm,
    ParticipantAdminForm,
    ParticipantForm,
    SelectMailForm,
    SelectParticipantForm,
    SelectParticipantSwitchForm,
)
from .models import Fahrt, FahrtMail, Participant
from .parser import Entry, parse_camt_csv


def get_confirmed_u18_participants_counts(semester: int) -> List[int]:
    participants: QuerySet[Participant] = Participant.objects.filter(
        Q(semester=semester) & Q(status="confirmed"),
    ).all()
    part_u18 = [participant.u18 for participant in participants]
    u18_count = len([participant for participant in part_u18 if participant])
    non_u18_count = len(part_u18) - u18_count
    return [u18_count, non_u18_count]


def get_confirmed_paid_participants_counts(semester: int) -> List[int]:
    paid_participants_count: int = (
        Participant.objects.exclude(paid=None).filter(Q(semester=semester) & Q(status="confirmed")).count()
    )
    unpaid_participants_count: int = Participant.objects.filter(
        Q(semester=semester) & Q(status="confirmed") & Q(paid=None),
    ).count()
    return [paid_participants_count, unpaid_participants_count]


def get_confirmed_non_liability_counts(semester: int) -> List[int]:
    submitted_non_liability_count: int = (
        Participant.objects.exclude(non_liability=None).filter(Q(semester=semester) & Q(status="confirmed")).count()
    )
    not_submitted_non_liability_count: int = Participant.objects.filter(
        Q(semester=semester) & Q(status="confirmed") & Q(non_liability=None),
    ).count()
    return [submitted_non_liability_count, not_submitted_non_liability_count]


def get_confirmed_participants_bachlor_master_counts(selected_semester: int) -> List[int]:
    participants: QuerySet[Participant] = Participant.objects.filter(
        Q(semester=selected_semester) & Q(status="confirmed"),
    )
    master_count: int = participants.filter(subject__degree=Subject.MASTER).count()
    bachlor_count: int = participants.filter(subject__degree=Subject.BACHELOR).count()
    return [bachlor_count, master_count]


@permission_required("fahrt.view_participants")
def fahrt_dashboard(request: WSGIRequest) -> HttpResponse:
    selected_semester: int = get_semester(request)
    confirmed_participants_by_studies = (
        Participant.objects.filter(Q(semester=selected_semester) & Q(status="confirmed"))
        .values("subject")
        .annotate(subject_count=Count("subject"))
        .order_by("subject_count")
    )
    participants_by_status = (
        Participant.objects.filter(semester=selected_semester)
        .values("status")
        .annotate(status_count=Count("status"))
        .order_by("status")
    )

    confirmed_participants_by_gender = (
        Participant.objects.filter(Q(semester=selected_semester) & Q(status="confirmed"))
        .values("gender")
        .annotate(gender_count=Count("gender"))
        .order_by("-gender")
    )

    confirmed_participants_by_food = (
        Participant.objects.filter(Q(semester=selected_semester) & Q(status="confirmed"))
        .values("nutrition")
        .annotate(nutrition_count=Count("nutrition"))
        .order_by("-nutrition")
    )

    confirmed_participants_allergy_list = (
        Participant.objects.filter(Q(semester=selected_semester) & Q(status="confirmed"))
        .exclude(allergies=None)
        .values("id", "allergies")
        .order_by("allergies")
    )

    context = {
        "participants_by_group_labels": [_(status["status"]) for status in participants_by_status],
        "participants_by_group_data": [status["status_count"] for status in participants_by_status],
        "confirmed_participants_by_studies_labels": [
            str(Subject.objects.get(pk=subject["subject"])) for subject in confirmed_participants_by_studies
        ],
        "confirmed_participants_by_studies_data": [
            subject["subject_count"] for subject in confirmed_participants_by_studies
        ],
        "confirmed_participants_by_food_labels": [
            _(nutrition["nutrition"]) for nutrition in confirmed_participants_by_food
        ],
        "confirmed_participants_by_food_data": [
            nutrition["nutrition_count"] for nutrition in confirmed_participants_by_food
        ],
        "confirmed_participants_by_gender_labels": [_(gender["gender"]) for gender in confirmed_participants_by_gender],
        "confirmed_participants_by_gender_data": [
            gender["gender_count"] for gender in confirmed_participants_by_gender
        ],
        "confirmed_participants_bachlor_master": get_confirmed_participants_bachlor_master_counts(
            selected_semester,
        ),
        "confirmed_participants_age": get_confirmed_u18_participants_counts(selected_semester),
        "confirmed_participants_paid": get_confirmed_paid_participants_counts(selected_semester),
        "confirmed_participants_non_liability": get_confirmed_non_liability_counts(
            selected_semester,
        ),
        "confirmed_participants_allergy_list": confirmed_participants_allergy_list,
    }
    return render(request, "fahrt/fahrt_dashboard.html", context)


@permission_required("fahrt.view_participants")
def list_registered(request: WSGIRequest) -> HttpResponse:
    semester = get_object_or_404(Semester, pk=get_semester(request))
    participants = semester.fahrt_participant.filter(status="registered").order_by(
        "-registration_time",
    )

    context = {
        "participants": participants,
    }
    return render(request, "fahrt/participants/list_registered.html", context)


@permission_required("fahrt.view_participants")
def list_waitinglist(request: WSGIRequest) -> HttpResponse:
    semester = get_object_or_404(Semester, pk=get_semester(request))
    participants = semester.fahrt_participant.filter(status="waitinglist").order_by(
        "-registration_time",
    )

    context = {
        "participants": participants,
    }
    return render(request, "fahrt/participants/list_waitinglist.html", context)


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
            participants = participants.filter(car=car)

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
    semester = get_object_or_404(Semester, pk=get_semester(request))
    filterform = FilterRegisteredParticipantsForm(request.POST or None, semester=semester)
    participants = get_possibly_filtered_participants(filterform, semester)

    u18s: int = sum(p.u18 for p in participants)
    allergies = participants.exclude(allergies="").count()

    number = participants.count()
    num_women = participants.filter(gender="female").count()
    proportion_of_women = int(num_women * 1.0 / number * 100) if number != 0 else 0

    places = participants.filter(car=True).aggregate(places=Sum("car_places"))["places"] or 0

    context = {
        "filterform": filterform,
        "nutritions": get_nutritunal_information(participants, semester),
        "participants": participants,
        "number": number,
        "non_liability": participants.filter(non_liability__isnull=False).count(),
        "paid": participants.filter(paid__isnull=False).count(),
        "places": places,
        "cars": participants.filter(car=True).count(),
        "u18s": u18s,
        "allergies": allergies,
        "num_women": num_women,
        "proportion_of_women": proportion_of_women,
    }
    return render(request, "fahrt/participants/list_confirmed.html", context)


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
    semester = get_object_or_404(Semester, pk=get_semester(request))
    participants = semester.fahrt_participant.filter(status="cancelled").order_by("surname")

    context = {
        "participants": participants,
    }
    return render(request, "fahrt/participants/list_cancelled.html", context)


@permission_required("fahrt.view_participants")
def view(request: WSGIRequest, participant_pk: int) -> HttpResponse:
    participant = get_object_or_404(Participant, pk=participant_pk)
    log_entries = participant.logentry_set.order_by("time")

    form = SelectMailForm(request.POST or None)

    if form.is_valid():
        mail = form.cleaned_data["mail"]
        request.session["selected_participants"] = [participant.id]

        return redirect("fahrt_sendmail", mail.id)

    context = {
        "participant": participant,
        "log_entries": log_entries,
        "form": form,
    }
    return render(request, "fahrt/participants/view_participant_details.html", context)


@permission_required("fahrt.view_participants")
def edit(request: WSGIRequest, participant_pk: int) -> HttpResponse:
    participant = get_object_or_404(Participant, pk=participant_pk)

    form = ParticipantAdminForm(
        request.POST or None,
        semester=participant.semester,
        instance=participant,
    )
    if form.is_valid():
        form.save()
        participant.log(request.user, "Participant edited")

        return redirect("fahrt_viewparticipant", participant.id)

    context = {
        "form": form,
        "participant": participant,
    }
    return render(request, "fahrt/participants/edit_participants.html", context)


@permission_required("fahrt.view_participants")
def delete(request: WSGIRequest, participant_pk: int) -> HttpResponse:
    participant = get_object_or_404(Participant, pk=participant_pk)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        participant.delete()

        return redirect("fahrt_index")

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

    return redirect("fahrt_viewparticipant", participant.id)


@permission_required("fahrt.view_participants")
def set_paid(request: WSGIRequest, participant_pk: int) -> HttpResponse:
    participant = get_object_or_404(Participant, pk=participant_pk)
    Participant.objects.filter(pk=participant_pk).update(
        paid=timezone.now().date(),
    )
    participant.log(request.user, "Set paid")

    return redirect("fahrt_viewparticipant", participant_pk)


@permission_required("fahrt.view_participants")
def set_nonliability(request: WSGIRequest, participant_pk: int) -> HttpResponse:
    participant = get_object_or_404(Participant, pk=participant_pk)
    Participant.objects.filter(pk=participant_pk).update(
        non_liability=timezone.now().date(),
    )
    participant.log(request.user, "Set non-liability")

    return redirect("fahrt_viewparticipant", participant_pk)


@permission_required("fahrt.view_participants")
def confirm(request: WSGIRequest, participant_pk: int) -> HttpResponse:
    participant = get_object_or_404(Participant, pk=participant_pk)
    Participant.objects.filter(pk=participant_pk).update(
        status="confirmed",
    )
    participant.log(request.user, "Confirmed")

    return redirect("fahrt_viewparticipant", participant_pk)


@permission_required("fahrt.view_participants")
def waitinglist(request: WSGIRequest, participant_pk: int) -> HttpResponse:
    participant = get_object_or_404(Participant, pk=participant_pk)
    Participant.objects.filter(pk=participant_pk).update(
        status="waitinglist",
    )
    participant.log(request.user, "On waitinglist")

    return redirect("fahrt_viewparticipant", participant_pk)


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

    return redirect("fahrt_viewparticipant", participant_pk)


@permission_required("fahrt.view_participants")
def cancel(request: WSGIRequest, participant_pk: int) -> HttpResponse:
    participant = get_object_or_404(Participant, pk=participant_pk)
    Participant.objects.filter(pk=participant_pk).update(
        status="cancelled",
    )
    participant.log(request.user, "Cancelled")

    return redirect("fahrt_viewparticipant", participant_pk)


def signup(request: WSGIRequest) -> HttpResponse:
    semester = get_object_or_404(Semester, pk=get_semester(request))
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
                non_liability = get_non_liability(participant.pk)
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

        return redirect("fahrt_signup_success")

    context = {
        "semester": semester,
        "form": form,
    }
    return render(request, "fahrt/standalone/signup.html", context)


@permission_required("fahrt.view_participants")
def signup_internal(request: WSGIRequest) -> HttpResponse:
    semester = get_object_or_404(Semester, pk=get_semester(request))

    try:
        semester.fahrt
    except ObjectDoesNotExist:
        messages.error(request, _("Please setup the SETtings for the Fahrt"))
        return redirect("fahrt_date")

    form = ParticipantForm(request.POST or None, semester=semester)
    if form.is_valid():
        participant = form.save()
        participant.log(request.user, "Signed up")
        mail = participant.semester.fahrt.mail_registration
        if mail:
            non_liability = get_non_liability(participant.pk)
            if not mail.send_mail_registration(participant, non_liability):
                messages.warning(
                    request,
                    _("Could not send the registration email. Make shure you configured the Registration-Mail."),
                )

        return redirect("fahrt_list_registered")

    context = {
        "semester": semester,
        "form": form,
    }
    return render(request, "fahrt/general/add_participant.html", context)


def signup_success(request: WSGIRequest) -> HttpResponse:
    return render(request, "fahrt/standalone/success.html")


@permission_required("fahrt.view_participants")
def filter_participants(request: WSGIRequest) -> HttpResponse:
    semester = get_object_or_404(Semester, pk=get_semester(request))

    participants = semester.fahrt_participant.order_by("surname")

    filterform = FilterParticipantsForm(request.POST or None)
    if filterform.is_valid():
        set_request_session_filtered_participants(filterform, participants, request)
        return redirect("fahrt_filteredparticipants")

    context = {
        "participants": participants,
        "filterform": filterform,
    }
    return render(request, "fahrt/mail/filter_participants_send_mail.html", context)


def set_request_session_filtered_participants(filterform, participants, request):
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
        participants = participants.filter(car=car)

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
    semester = get_object_or_404(Semester, pk=get_semester(request))
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
        return redirect("fahrt_sendmail", mail.id)

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
    return render(request, "fahrt/mail/list_filtered_participants_send_mail.html", context)


@permission_required("fahrt.view_participants")
def index_mails(request: WSGIRequest) -> HttpResponse:
    context = {"mails": FahrtMail.objects.all()}
    return render(request, "fahrt/mail/index_mails.html", context)


@permission_required("fahrt.view_participants")
def add_mail(request: WSGIRequest) -> HttpResponse:
    form = MailForm(request.POST or None)
    if form.is_valid():
        form.save()

        return redirect("fahrt_listmails")

    context = {"form": form, "mail": FahrtMail}
    return render(request, "fahrt/mail/add_mail.html", context)


@permission_required("fahrt.view_participants")
def edit_mail(request: WSGIRequest, mail_pk: int) -> HttpResponse:
    mail = get_object_or_404(FahrtMail, pk=mail_pk)

    form = MailForm(request.POST or None, instance=mail)
    if form.is_valid():
        form.save()

        return redirect("fahrt_listmails")

    context = {
        "form": form,
        "mail": mail,
    }
    return render(request, "fahrt/mail/edit_mail.html", context)


@permission_required("fahrt.view_participants")
def delete_mail(request: WSGIRequest, mail_pk: int) -> HttpResponse:
    mail = get_object_or_404(FahrtMail, pk=mail_pk)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        mail.delete()

        return redirect("fahrt_listmails")

    context = {
        "mail": mail,
        "form": form,
    }
    return render(request, "fahrt/mail/del_mail.html", context)


@permission_required("fahrt.view_participants")
def send_mail(request: WSGIRequest, mail_pk: int) -> HttpResponse:
    mail: FahrtMail = get_object_or_404(FahrtMail, pk=mail_pk)
    selected_participants = request.session["selected_participants"]
    semester = get_object_or_404(Semester, pk=get_semester(request))
    participants = semester.fahrt_participant.filter(id__in=selected_participants).order_by("surname")

    subject, text, from_email = mail.get_mail_participant()

    form = forms.Form(request.POST or None)
    failed_participants = []
    if form.is_valid():
        for participant in participants:
            success = mail.send_mail_participant(participant)
            if success:
                participant.log(request.user, f"Mail '{mail}' sent")
            else:
                failed_participants.append(participant)
        if not failed_participants:
            return redirect("fahrt_filter")

    context = {
        "participants": participants,
        "failed_participants": failed_participants,
        "subject": subject,
        "text": text,
        "from_email": from_email,
        "form": form,
    }

    if failed_participants:
        return render(request, "fahrt/mail/send_mail_failure.html", context)
    return render(request, "fahrt/mail/send_mail.html", context)


@permission_required("fahrt.view_participants")
def change_date(request: WSGIRequest) -> HttpResponse:
    semester = get_object_or_404(Semester, pk=get_semester(request))

    try:
        fahrt = semester.fahrt
    except ObjectDoesNotExist:
        fahrt = Fahrt.objects.create(
            semester=semester,
            date=timezone.now().date(),
            open_registration=timezone.now(),
            close_registration=timezone.now(),
        )

    form = FahrtForm(request.POST or None, instance=fahrt)
    if form.is_valid():
        form.save()
        return redirect("fahrt_index")

    context = {
        "form": form,
    }
    return render(request, "fahrt/general/settings.html", context)


@permission_required("fahrt.view_participants")
def export(request: WSGIRequest, file_format: str = "csv") -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    try:
        fahrt = semester.fahrt
    except ObjectDoesNotExist:
        messages.error(request, _("Please setup the SETtings for the Fahrt"))
        return redirect("fahrt_date")
    participants = semester.fahrt_participant.order_by("surname", "firstname")
    filename = f"fahrt_participants_{fahrt.semester}_{fahrt.date}_{time.strftime('%Y%m%d-%H%M')}"
    context = {"participants": participants, "fahrt": fahrt}
    if file_format == "csv":
        return utils.download_csv(
            [
                "surname",
                "firstname",
                "birthday",
                "email",
                "phone",
                "mobile",
                "subject",
                "nutrition",
                "allergies",
            ],
            f"{filename}.csv",
            participants,
        )
    return utils.download_pdf("fahrt/tex/participants.tex", f"{filename}.pdf", context)


@permission_required("fahrt.view_participants")
def non_liability_form(request: WSGIRequest, participant_pk: int) -> HttpResponse:
    return get_non_liability(participant_pk)


def get_non_liability(participant_pk: int) -> HttpResponse:
    participant: Participant = get_object_or_404(Participant, pk=participant_pk)
    fahrt: Fahrt = get_object_or_404(Fahrt, semester=participant.semester)
    context = {
        "participant": participant,
        "fahrt": fahrt,
    }
    filename = f"non_liability_{participant.surname}_{participant.firstname}.pdf"
    if participant.u18:
        return utils.download_pdf("fahrt/tex/u18_non_liability.tex", filename, context)
    return utils.download_pdf("fahrt/tex/ü18_non_liability.tex", filename, context)


@permission_required("fahrt.view_participants")
def fahrt_finanz_simple(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    fahrt: Fahrt = get_object_or_404(Fahrt, semester=semester)
    participants: List[Participant] = list(Participant.objects.filter(semester=semester, status="confirmed").all())
    select_participant_form_set = formset_factory(SelectParticipantSwitchForm, extra=0)
    participantforms = select_participant_form_set(
        request.POST or None,
        initial=[{"id": p.id, "selected": p.paid is not None} for p in participants],
    )

    if participantforms.is_valid():
        new_paid_participants: List[Participant] = []
        new_unpaid_participants: List[Participant] = []
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
                if Participant.objects.filter(id=participant_id, paid__isnull=True).exists():
                    new_paid_participants.append(participant_id)
            else:
                if Participant.objects.filter(id=participant_id, paid__isnull=False).exists():
                    new_unpaid_participants.append(participant_id)
        if new_paid_participants or new_unpaid_participants:
            request.session["new_paid_participants"] = new_paid_participants
            request.session["new_unpaid_participants"] = new_unpaid_participants
            return redirect("fahrt_finanz_confirm")

    participants_and_select = []
    for participant in participants:
        for participant_form in participantforms:
            if participant_form.initial["id"] == participant.id:
                participants_and_select.append((participant, participant_form))
                break
    context = {
        "fahrt": fahrt,
        "participants_and_select": participants_and_select,
        "participantforms": participantforms,
    }
    return render(request, "fahrt/finanz/simple_finanz.html", context)


@permission_required("fahrt.view_participants")
def fahrt_finanz_confirm(request: WSGIRequest) -> HttpResponse:
    new_paid_participants = [
        Participant.objects.get(id=part_id) for part_id in request.session["new_paid_participants"]
    ]
    new_unpaid_participants = [
        Participant.objects.get(id=part_id) for part_id in request.session["new_unpaid_participants"]
    ]
    form = forms.Form(request.POST or None)
    if form.is_valid():
        for new_paid_participant in new_paid_participants:
            new_paid_participant.paid = date.today()
            new_paid_participant.save()
        for new_unpaid_participant in new_unpaid_participants:
            new_unpaid_participant.paid = None
            new_unpaid_participant.save()
        messages.success(request, _("Saved changed payment status"))
        return redirect("fahrt_finanz_simple")

    context = {
        "form": form,
        "new_paid_participants": new_paid_participants,
        "new_unpaid_participants": new_unpaid_participants,
    }
    return render(request, "fahrt/finanz/finanz_confirmation.html", context)


@permission_required("bags.view_participants")
def fahrt_finanz_automated(request: WSGIRequest) -> HttpResponse:
    file_upload_form = CSVFileUploadForm(request.POST or None, request.FILES)

    if file_upload_form.is_valid():
        csv_file: Optional[UploadedFile] = request.FILES.get("file")
        if csv_file is None:
            raise Http404
        csv_file_text = TextIOWrapper(csv_file.file, encoding="iso-8859-1")
        results, errors = parse_camt_csv(csv_file_text)
        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect("fahrt_finanz_automated")
        request.session["results"] = results
        messages.success(request, _("The File was successfully uploaded"))
        return redirect("fahrt_finanz_auto_matching")

    context = {
        "form": file_upload_form,
    }
    return render(request, "fahrt/finanz/automated_finanz.html", context)


@permission_required("bags.view_participants")
def fahrt_finanz_auto_matching(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    participants: QuerySet[Participant] = Participant.objects.filter(semester=semester, status="confirmed")
    transactions: List[Entry] = [Entry.from_json(entry) for entry in request.session["results"]]

    for transaction in transactions:
        pass

    context = {
        "matched_transactions": None,
        "unmatched_transactions": None,
    }
    return render(request, "fahrt/finanz/automated_finanz_matching.html", context)
