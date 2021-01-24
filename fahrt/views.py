from datetime import date
from datetime import timedelta
from typing import Dict
from typing import List
from typing import Union

from django import forms
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from django.db.models import Q
from django.db.models import QuerySet
from django.db.models import Sum
from django.forms import formset_factory
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from settool_common.models import get_semester
from settool_common.models import Semester
from settool_common.models import Subject

from .forms import FahrtForm
from .forms import FilterParticipantsForm
from .forms import MailForm
from .forms import ParticipantAdminForm
from .forms import ParticipantForm
from .forms import SelectMailForm
from .forms import SelectParticipantForm
from .models import Fahrt
from .models import Mail
from .models import Participant


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
        Participant.objects.exclude(paid=None)
        .filter(Q(semester=semester) & Q(status="confirmed"))
        .count()
    )
    unpaid_participants_count: int = Participant.objects.filter(
        Q(semester=semester) & Q(status="confirmed") & Q(paid=None),
    ).count()
    return [paid_participants_count, unpaid_participants_count]


def get_confirmed_non_liability_counts(semester: int) -> List[int]:
    submitted_non_liability_count: int = (
        Participant.objects.exclude(non_liability=None)
        .filter(Q(semester=semester) & Q(status="confirmed"))
        .count()
    )
    not_submitted_non_liability_count: int = Participant.objects.filter(
        Q(semester=semester) & Q(status="confirmed") & Q(non_liability=None),
    ).count()
    return [submitted_non_liability_count, not_submitted_non_liability_count]


def get_confirmed_participants_bachlor_master_counts(selected_semester):
    participants = Participant.objects.filter(Q(semester=selected_semester) & Q(status="confirmed"))
    master_count = participants.filter(subject__degree=Subject.MASTER).count()
    bachlor_count = participants.filter(subject__degree=Subject.BACHELOR).count()
    return [bachlor_count, master_count]


@permission_required("fahrt.view_participants")
def fahrt_dashboard(request):
    selected_semester: int = get_semester(request)
    confirmed_participants_by_studies: List[Dict[str, Union[str, int]]] = (
        Participant.objects.filter(Q(semester=selected_semester) & Q(status="confirmed"))
        .values("subject")
        .annotate(subject_count=Count("subject"))
        .order_by("subject_count")
    )
    participants_by_status: List[Dict[str, Union[str, int]]] = (
        Participant.objects.filter(semester=selected_semester)
        .values("status")
        .annotate(status_count=Count("status"))
        .order_by("status")
    )

    confirmed_participants_by_gender: List[Dict[str, Union[str, int]]] = (
        Participant.objects.filter(Q(semester=selected_semester) & Q(status="confirmed"))
        .values("gender")
        .annotate(gender_count=Count("gender"))
        .order_by("-gender")
    )

    confirmed_participants_by_food: List[Dict[str, Union[str, int]]] = (
        Participant.objects.filter(Q(semester=selected_semester) & Q(status="confirmed"))
        .values("nutrition")
        .annotate(nutrition_count=Count("nutrition"))
        .order_by("-nutrition")
    )

    confirmed_participants_allergy_list: List[Dict[str, Union[str, int]]] = (
        Participant.objects.filter(Q(semester=selected_semester) & Q(status="confirmed"))
        .exclude(allergies=None)
        .values("id", "allergies")
        .order_by("allergies")
    )

    context = {
        "participants_by_group_labels": [_(status["status"]) for status in participants_by_status],
        "participants_by_group_data": [status["status_count"] for status in participants_by_status],
        "confirmed_participants_by_studies_labels": [
            str(Subject.objects.get(pk=subject["subject"]))
            for subject in confirmed_participants_by_studies
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
        "confirmed_participants_by_gender_labels": [
            _(gender["gender"]) for gender in confirmed_participants_by_gender
        ],
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
def list_registered(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    participants = semester.fahrt_participant.filter(status="registered").order_by("surname")

    context = {
        "participants": participants,
    }
    return render(request, "fahrt/participants/list_registered.html", context)


@permission_required("fahrt.view_participants")
def list_waitinglist(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    participants = semester.fahrt_participant.filter(status="waitinglist").order_by("surname")

    context = {
        "participants": participants,
    }
    return render(request, "fahrt/participants/list_waitinglist.html", context)


@permission_required("fahrt.view_participants")
def list_confirmed(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    participants = semester.fahrt_participant.filter(status="confirmed").order_by(
        "payment_deadline",
        "surname",
        "firstname",
    )

    u18s = [p for p in participants if p.u18]
    allergies = participants.exclude(allergies="").count()

    number = participants.count()
    num_women = participants.filter(gender="female").count()
    if number == 0:
        proportion_of_women = 0
    else:
        proportion_of_women = int(num_women * 1.0 / number * 100)

    places = participants.filter(car=True).aggregate(places=Sum("car_places"))
    places = places["places"] or 0

    context = {
        "nutritions": get_nutritunal_information(participants, semester),
        "participants": participants,
        "number": number,
        "non_liability": participants.filter(
            non_liability__isnull=False,
        ).count(),
        "paid": participants.filter(paid__isnull=False).count(),
        "places": places,
        "cars": participants.filter(car=True).count(),
        "u18s": len(u18s),
        "allergies": allergies,
        "num_women": num_women,
        "proportion_of_women": proportion_of_women,
    }
    return render(request, "fahrt/participants/list_confirmed.html", context)


def get_nutritunal_information(
    participants: QuerySet[Participant],
    semester: Semester,
) -> List[Dict[str, object]]:
    nutrition_choices = [
        choice["nutrition"]
        for choice in semester.fahrt_participant.filter(status="confirmed")
        .values("nutrition")
        .distinct()
    ]
    return [
        (
            {
                "name": choice,
                "count": str(participants.filter(nutrition=choice).count()),
                "allergies": participants.filter(nutrition=choice)
                .exclude(allergies="")
                .values("allergies"),
            }
        )
        for choice in nutrition_choices
    ]


@permission_required("fahrt.view_participants")
def list_cancelled(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    participants = semester.fahrt_participant.filter(status="cancelled").order_by("surname")

    context = {
        "participants": participants,
    }
    return render(request, "fahrt/participants/list_cancelled.html", context)


@permission_required("fahrt.view_participants")
def view(request, participant_pk):
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
def edit(request, participant_pk):
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
def delete(request, participant_pk):
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
def toggle_mailinglist(request, participant_pk):
    participant = get_object_or_404(Participant, pk=participant_pk)
    Participant.objects.filter(pk=participant_pk).update(
        mailinglist=(not participant.mailinglist),
    )
    participant = get_object_or_404(Participant, pk=participant_pk)
    participant.toggle_mailinglist()  # TODO does nothing
    participant.log(request.user, "Toggle mailinglist")

    return redirect("fahrt_viewparticipant", participant.id)


@permission_required("fahrt.view_participants")
def set_paid(request, participant_pk):
    participant = get_object_or_404(Participant, pk=participant_pk)
    Participant.objects.filter(pk=participant_pk).update(
        paid=timezone.now().date(),
    )
    participant.log(request.user, "Set paid")

    return redirect("fahrt_viewparticipant", participant_pk)


@permission_required("fahrt.view_participants")
def set_nonliability(request, participant_pk):
    participant = get_object_or_404(Participant, pk=participant_pk)
    Participant.objects.filter(pk=participant_pk).update(
        non_liability=timezone.now().date(),
    )
    participant.log(request.user, "Set non-liability")

    return redirect("fahrt_viewparticipant", participant_pk)


@permission_required("fahrt.view_participants")
def confirm(request, participant_pk):
    participant = get_object_or_404(Participant, pk=participant_pk)
    Participant.objects.filter(pk=participant_pk).update(
        status="confirmed",
    )
    participant.log(request.user, "Confirmed")

    return redirect("fahrt_viewparticipant", participant_pk)


@permission_required("fahrt.view_participants")
def waitinglist(request, participant_pk):
    participant = get_object_or_404(Participant, pk=participant_pk)
    Participant.objects.filter(pk=participant_pk).update(
        status="waitinglist",
    )
    participant.log(request.user, "On waitinglist")

    return redirect("fahrt_viewparticipant", participant_pk)


@permission_required("fahrt.view_participants")
def set_payment_deadline(request, participant_pk, weeks):
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
def cancel(request, participant_pk):
    participant = get_object_or_404(Participant, pk=participant_pk)
    Participant.objects.filter(pk=participant_pk).update(
        status="cancelled",
    )
    participant.log(request.user, "Cancelled")

    return redirect("fahrt_viewparticipant", participant_pk)


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
        return render(request, "fahrt/standalone/registration_closed.html", {})

    form = ParticipantForm(request.POST or None, semester=semester)
    if form.is_valid():
        participant = form.save()
        participant.log(None, "Signed up")

        return redirect("fahrt_signup_success")

    context = {
        "semester": semester,
        "form": form,
    }
    return render(request, "fahrt/standalone/signup.html", context)


@permission_required("fahrt.view_participants")
def signup_internal(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)

    form = ParticipantForm(request.POST or None, semester=semester)
    if form.is_valid():
        participant = form.save()
        participant.log(request.user, "Signed up")

        return redirect("fahrt_list_registered")

    context = {
        "semester": semester,
        "form": form,
    }
    return render(request, "fahrt/general/add_participant.html", context)


def signup_success(request):
    return render(request, "fahrt/standalone/success.html", {})


@permission_required("fahrt.view_participants")
def filter_participants(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)

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
            Q(firstname__icontains=search)
            | Q(surname__icontains=search)
            | Q(comment__icontains=search),
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
def filtered_list(request):
    filtered_participants = request.session["filtered_participants"]
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    participants = semester.fahrt_participant.filter(
        id__in=filtered_participants,
    ).order_by("surname")

    form = SelectMailForm(request.POST or None, semester=semester)
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
def index_mails(request):
    context = {"mails": Mail.objects.all()}
    return render(request, "fahrt/mail/index_mails.html", context)


@permission_required("fahrt.view_participants")
def add_mail(request):

    form = MailForm(request.POST or None)
    if form.is_valid():
        form.save()

        return redirect("fahrt_listmails")

    context = {"form": form}
    return render(request, "fahrt/mail/add_mail.html", context)


@permission_required("fahrt.view_participants")
def edit_mail(request, mail_pk):
    mail = get_object_or_404(Mail, pk=mail_pk)

    form = MailForm(request.POST or None, instance=mail)
    if form.is_valid():
        form.save()

        return redirect("fahrt_listmails")

    context = {
        "form": form,
        "mail": mail,
    }
    return render(request, "fahrt/standalone/edit_mail.html", context)


@permission_required("fahrt.view_participants")
def delete_mail(request, mail_pk):
    mail = get_object_or_404(Mail, pk=mail_pk)

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
def send_mail(request, mail_pk):
    mail = get_object_or_404(Mail, pk=mail_pk)
    selected_participants = request.session["selected_participants"]
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    participants = semester.fahrt_participant.filter(
        id__in=selected_participants,
    ).order_by("surname")

    subject, text, from_email = mail.get_mail()

    form = forms.Form(request.POST or None)
    failed_participants = []
    if form.is_valid():
        for participant in participants:
            success = mail.send_mail(participant)
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

    form = FahrtForm(request.POST or None, instance=fahrt)
    if form.is_valid():
        form.save()
        return redirect("fahrt_date")

    context = {
        "form": form,
    }
    return render(request, "fahrt/general/change_date.html", context)
