from datetime import date
from io import TextIOWrapper
from typing import Optional
from uuid import UUID

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.files.uploadedfile import UploadedFile
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import QuerySet
from django.forms import formset_factory
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from settool_common.models import get_semester, Semester

from ..forms import CSVFileUploadForm, ParticipantSelectForm, SelectParticipantSwitchForm
from ..models import Fahrt, Participant
from ..parser import Entry, parse_camt_csv


@permission_required("finanz")
def finanz_simple(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    fahrt: Fahrt = get_object_or_404(Fahrt, semester=semester)
    participants: list[Participant] = list(Participant.objects.filter(semester=semester, status="confirmed").all())

    select_participant_form_set = formset_factory(SelectParticipantSwitchForm, extra=0)
    participantforms = select_participant_form_set(
        request.POST or None,
        initial=[{"id": p.id, "selected": p.paid is not None} for p in participants],
    )

    if participantforms.is_valid():
        new_paid_participants: list[int] = []
        new_unpaid_participants: list[int] = []
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
            return redirect("fahrt:finanz_confirm")

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


@permission_required("finanz")
def finanz_confirm(request: WSGIRequest) -> HttpResponse:
    new_paid_participants: list[Participant] = [
        Participant.objects.get(id=part_id) for part_id in request.session["new_paid_participants"]
    ]
    new_unpaid_participants: list[Participant] = [
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
        return redirect("fahrt:finanz_simple")

    context = {
        "form": form,
        "new_paid_participants": new_paid_participants,
        "new_unpaid_participants": new_unpaid_participants,
    }
    return render(request, "fahrt/finanz/finanz_confirmation.html", context)


@permission_required("finanz")
def finanz_automated(request: WSGIRequest) -> HttpResponse:
    file_upload_form = CSVFileUploadForm(request.POST or None, request.FILES)

    if file_upload_form.is_valid():
        csv_file: Optional[UploadedFile] = request.FILES.get("file")
        if csv_file is None:
            raise Http404()  # cannot happen, as file_upload_form would not be valid
        csv_file_text = TextIOWrapper(csv_file.file, encoding="iso-8859-1")
        results, errors = parse_camt_csv(csv_file_text)
        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect("fahrt:finanz_automated")
        request.session["results"] = results
        messages.success(request, _("The File was successfully uploaded"))
        return redirect("fahrt:finanz_auto_matching")

    context = {
        "form": file_upload_form,
    }
    return render(request, "fahrt/finanz/automated_finanz.html", context)


@permission_required("finanz")
def finanz_auto_matching(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    participants: QuerySet[Participant] = Participant.objects.filter(semester=semester, status="confirmed")

    # mypy is weird for this one. equivalent [but not Typechecking]:  participants.values_list("uuid", flat=True)
    participants_ids_pre_mypy: list[Optional[UUID]] = [element["uuid"] for element in participants.values("uuid")]
    participants_ids: list[UUID] = [uuid for uuid in participants_ids_pre_mypy if uuid]

    transactions: list[Entry] = [Entry.from_json(entry) for entry in request.session["results"]]

    error, matched_transactions, unmatched_transactions = match_transactions_participant_ids(
        participants_ids,
        request,
        transactions,
    )
    if error:
        return redirect("fahrt:finanz_automated")

    # genrerate selection boxes
    unmatched_trans_form_set = formset_factory(ParticipantSelectForm, extra=len(unmatched_transactions))
    forms_unmatched = unmatched_trans_form_set(request.POST or None, form_kwargs={"semester": semester})
    forms_unmatched_trans = list(zip(forms_unmatched, unmatched_transactions))
    matched_trans_form_set = formset_factory(ParticipantSelectForm, extra=0)
    forms_matched = matched_trans_form_set(
        request.POST or None,
        initial=[{"selected": p_uuid} for (p_uuid, _) in matched_transactions],
        form_kwargs={"semester": semester},
    )
    forms_matched_trans = []
    for p_uuid, transaction in matched_transactions:
        for p_form in forms_matched:
            if p_form.initial["selected"] == p_uuid:
                forms_matched_trans.append((p_form, transaction))
                break

    # parse forms and redirect to confirmation page
    if forms_unmatched.is_valid() and forms_matched.is_valid():
        # hs notation: fst(unzip xs)++fst(unzip ys)
        selection_forms = []
        if forms_matched_trans:
            selection_forms += list(zip(*forms_matched_trans))[0]
        if forms_unmatched_trans:
            selection_forms += list(zip(*forms_unmatched_trans))[0]
        new_paid_participants = set()
        for form in selection_forms:
            if form.cleaned_data:
                selected_part: Participant = form.cleaned_data["selected"]
                if selected_part and Participant.objects.get(id=selected_part.id).paid is None:
                    new_paid_participants.add(selected_part.id)

        if new_paid_participants:
            request.session["new_paid_participants"] = list(new_paid_participants)
            request.session["new_unpaid_participants"] = []
            return redirect("fahrt:finanz_confirm")
        messages.warning(request, _("No Changes to Payment-state detected"))
        return redirect("fahrt:finanz_automated")

    context = {
        "matched_transactions": forms_matched_trans,
        "unmatched_transactions": forms_unmatched_trans,
        "forms_matched": forms_matched,
        "forms_unmatched": forms_unmatched,
    }
    return render(request, "fahrt/finanz/automated_finanz_matching.html", context)


def match_transactions_participant_ids(
    participants_ids: list[UUID],
    request: WSGIRequest,
    transactions: list[Entry],
) -> tuple[bool, list[tuple[UUID, Entry]], list[Entry]]:
    participant_matches: dict[UUID, list[Entry]] = {p_uuid: [] for p_uuid in participants_ids}
    matched_transactions: list[tuple[UUID, Entry]] = []
    unmatched_transactions: list[Entry] = []
    error = False

    transaction: Entry
    for transaction in transactions:
        matches: list[UUID] = [p_uuid for p_uuid in participants_ids if str(p_uuid) in transaction.verwendungszweck]
        if matches:
            for match in matches:
                matched_transactions.append((match, transaction))
                participant_matches[match].append(transaction)
            # Transaction:Person = 1:1
            if len(matches) > 1:
                messages.error(
                    request,
                    _("Transaction {transaction} contains multiple UUIDs (matches). This is not allowed.").format(
                        transaction=transaction.__repr__(),
                        matches=matches,
                    ),
                )
                error = True
        else:
            unmatched_transactions.append(transaction)
    # Transaction:Person = 1:1
    for (p_uuid, transaction_list) in participant_matches.items():
        if len(transaction_list) >= 2:
            messages.error(
                request,
                _(
                    "UUIDs {p_uuid} is contained in multiple Transactions {transaction_list}. This is not allowed.",
                ).format(
                    p_uuid=p_uuid,
                    transaction_list=transaction_list,
                ),
            )
            error = True
    return error, matched_transactions, unmatched_transactions
