from typing import Any, Optional
from uuid import UUID

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.handlers.wsgi import WSGIRequest
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from settool_common.models import get_semester, Semester

from ..forms import (
    AddParticipantToTransportForm,
    ParticipantSelectForm,
    TransportAdminOptionForm,
    TransportationCommentForm,
    TransportOptionForm,
)
from ..models import Fahrt, Participant, Transportation


def get_transport_types(fahrt: Fahrt) -> list[tuple[str, str, int, Any]]:
    return [
        (
            _("Cars"),
            _("Car"),
            Transportation.CAR,
            Transportation.objects.filter(transport_type=Transportation.CAR, fahrt=fahrt),
        ),
        (
            _("Trains"),
            _("Train"),
            Transportation.TRAIN,
            Transportation.objects.filter(transport_type=Transportation.TRAIN, fahrt=fahrt),
        ),
    ]


def transport_participant(request: WSGIRequest, participant_uuid: UUID) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    participant: Participant = get_object_or_404(Participant, pk=participant_uuid, status="confirmed")
    context = {
        "transport_types": get_transport_types(semester.fahrt),
        "calling_participant": participant,
    }
    return render(request, "fahrt/transportation/participant/list_transports.html", context)


def add_transport_option(request: WSGIRequest, participant_uuid: UUID, transport_type: int) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))

    try:
        fahrt: Fahrt = semester.fahrt
    except ObjectDoesNotExist:
        messages.error(
            request,
            _(
                "The Admins have not created a Fahrt for the Semester you are in. "
                "Please contact them with this error message.",
            ),
        )
        return redirect("fahrt:transport_participant", participant_uuid)

    participant: Participant = get_object_or_404(Participant, pk=participant_uuid, status="confirmed")
    if transport_type not in [Transportation.CAR, Transportation.TRAIN]:
        raise Http404()
    transport: Optional[Transportation] = participant.transportation
    if transport and transport.creator == participant:
        if transport.transport_type == transport_type:
            messages.error(request, _("You can not create a new Transport-option of the same type"))
            return redirect("fahrt:transport_participant", participant_uuid)
        if transport.participant_set.count() != 1:
            messages.error(
                request,
                _("A Transportation-option cannot be without creator, if it has people depending upon it."),
            )
            return redirect("fahrt:transport_participant", participant_uuid)

    form = TransportOptionForm(
        request.POST or None,
        transport_type=transport_type,
        creator=participant,
        fahrt=fahrt,
    )
    if form.is_valid():
        if transport and transport.creator == participant:
            transport.delete()  # we checked before that we are the only participant of this Transport option
        form.save(commit=True)
        participant.log(
            None,
            _("created Transport Option {transport} and assigned him/herself").format(transport=transport),
        )
        return redirect("fahrt:transport_participant", participant_uuid)
    context = {
        "form": form,
        "calling_participant": participant,
    }
    return render(request, "fahrt/transportation/participant/add_transport.html", context)


def add_transport_participant(request: WSGIRequest, participant_uuid: UUID, transport_pk: int) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    participant: Participant = get_object_or_404(Participant, pk=participant_uuid, status="confirmed")
    new_transport: Transportation = get_object_or_404(Transportation, id=transport_pk, fahrt=semester.fahrt)

    transport: Optional[Transportation] = participant.transportation
    if transport and transport.creator == participant and transport.participant_set.count() != 1:
        messages.error(
            request,
            _("A Transportation-option cannot be without creator, if it has people depending upon it."),
        )
        return redirect("fahrt:transport_participant", participant_uuid)

    if new_transport.participant_set.count() < new_transport.places:

        if transport and transport.creator == participant:
            transport.delete()  # we checked before that we are the only participant of this Transport option
        participant.transportation = new_transport
        participant.save()
        participant.log(None, _("added him/herself to Transport Option {transport}").format(transport=new_transport))
    else:
        messages.error(request, _("The selected option seems to be full"))

    return redirect("fahrt:transport_participant", participant_uuid)


@permission_required("fahrt.view_participants")
def transport_mangagement(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    try:
        fahrt: Fahrt = semester.fahrt
    except ObjectDoesNotExist:
        messages.error(request, _("You have to create Fahrt Settings to manage the fahrt"))
        return redirect("fahrt:settings")
    context = {"transport_types": get_transport_types(fahrt)}
    return render(
        request,
        "fahrt/transportation/management/list_transports.html",
        context,
    )


@permission_required("fahrt.view_participants")
def add_transport_option_by_management(request: WSGIRequest, transport_type: int) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    if transport_type not in [Transportation.CAR, Transportation.TRAIN]:
        raise Http404()
    try:
        fahrt: Fahrt = semester.fahrt
    except ObjectDoesNotExist:
        messages.error(request, _("You have to create Fahrt Settings to manage the fahrt"))
        return redirect("fahrt:settings")

    form = TransportAdminOptionForm(request.POST or None, transport_type=transport_type, fahrt=fahrt)
    if form.is_valid():
        transport: Transportation = form.save(commit=True)
        if transport.creator:  # for mypy
            transport.creator.log(
                request.user,
                _("created Transport Option {transport} and assigned participant").format(transport=transport),
            )
        return redirect("fahrt:transport_mangagement")
    context = {
        "form": form,
    }
    return render(request, "fahrt/transportation/management/add_transport.html", context)


@permission_required("fahrt.view_participants")
def add_transport_participant_by_management(request: WSGIRequest, transport_pk: int) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    transport: Transportation = Transportation.objects.get(id=transport_pk)
    form = AddParticipantToTransportForm(request.POST or None, semester=semester)
    if form.is_valid():
        person: Participant = form.cleaned_data["person"]
        if transport.participant_set.count() < transport.places:
            person.transportation = transport
            person.save()
            person.log(
                request.user,
                _("added to Transport Option {transport} and assigned pariticipant").format(transport=transport),
            )
        else:
            messages.error(request, _("The Selected option seems to be full"))
        return redirect("fahrt:transport_mangagement")
    context = {"transport": transport, "form": form}
    return render(
        request,
        "fahrt/transportation/management_only/add_participant_to_transport.html",
        context,
    )


@permission_required("fahrt.view_participants")
def edit_transport_participant_by_management(request: WSGIRequest, participant_uuid: UUID) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    participant: Participant = get_object_or_404(Participant, pk=participant_uuid, status="confirmed")
    transport: Optional[Transportation] = participant.transportation

    form = ParticipantSelectForm(request.POST or None, semester=semester)
    if form.is_valid():
        participant2: Participant = form.cleaned_data["selected"]
        if participant2 == participant:
            messages.warning(request, _("Succesfully exchanged {p1} with itsself :)").format(p1=participant))
            return redirect("fahrt:transport_mangagement")

        transport_2: Optional[Transportation] = participant2.transportation
        transport_creator_1_has_to_change = transport and transport.creator == participant
        transport_creator_2_has_to_change = transport_2 and transport_2.creator == participant2
        # possibly exchanging creators
        if transport and transport_2 and transport_creator_1_has_to_change and transport_creator_2_has_to_change:
            # redundant typechecking is due to mypy
            transport.creator = None
            transport.save()
            transport_2.creator = participant
            transport_2.save()
            transport.creator = participant2
            transport.save()
        elif transport and transport_creator_1_has_to_change:  # redundant typechecking is due to mypy
            transport.creator = participant2
            transport.save()
        elif transport_2 and transport_creator_2_has_to_change:  # redundant typechecking is due to mypy
            transport_2.creator = participant
            transport_2.save()
        # possibly exchanging transportation
        participant.transportation = transport_2
        participant.save()
        participant.log(request.user, f"Exchanged transport option with {participant2}")

        participant2.transportation = transport
        participant2.save()
        participant2.log(request.user, f"Exchanged transport option with {participant}")
        messages.success(request, _("Succesfully exchanged {p1} and {p2}").format(p1=participant, p2=participant2))
        return redirect("fahrt:transport_mangagement")

    context = {
        "form": form,
        "calling_participant": participant,
        "transport": transport,
    }
    return render(request, "fahrt/transportation/management_only/edit_participant_transport.html", context)


@permission_required("fahrt.view_participants")
def del_transport_participant_by_management(request: WSGIRequest, participant_uuid: UUID) -> HttpResponse:
    participant: Participant = get_object_or_404(Participant, pk=participant_uuid, status="confirmed")
    transport: Optional[Transportation] = participant.transportation
    if transport is None:
        messages.warning(
            request,
            _(
                "This participant is not assigned to a transport option. this can Thus not be deleted. You can however "
                "create a new transport option for this participant",
            ),
        )
        return redirect("fahrt:transport_participant", participant_uuid)

    if transport.creator == participant and transport.participant_set.count() > 1:
        messages.error(
            request,
            _(
                "The Transportation option of the Creator of a Transportation option can NOT be deleted if his "
                "Transportation option has participants left",
            ),
        )
        return redirect("fahrt:transport_mangagement")

    form = forms.Form(request.POST or None)
    if form.is_valid():
        if transport and transport.creator == participant:
            transport.delete()  # we checked before that we are the only participant of this Transport option
        participant.transportation = None
        participant.save()
        participant.log(request.user, "Deleted transport option")
        messages.success(
            request,
            _("Succesfully deleted transport option of {participant}").format(participant=participant),
        )
        return redirect("fahrt:transport_mangagement")

    context = {
        "form": form,
        "calling_participant": participant,
        "transport": transport,
    }
    return render(request, "fahrt/transportation/management_only/del_participant_transport.html", context)


def transport_chat(request: WSGIRequest, participant_uuid: UUID, transport_pk: int) -> HttpResponse:
    participant: Participant = get_object_or_404(Participant, pk=participant_uuid, status="confirmed")
    transport: Transportation = get_object_or_404(Transportation, pk=transport_pk)
    if not participant.publish_contact_to_other_paricipants:
        messages.warning(
            request,
            _(
                "You have chosen to not discose your name and most relevant contact info to other participants. We "
                "respect that choice and thus hide your personal data even here.",
            ),
        )
    messages.info(
        request,
        _(
            "Currently this is only a Chatwall and not a Live-Chat. This means you have to refresh the page to get "
            "new messages.",
        ),
    )

    form = TransportationCommentForm(request.POST or None, transport=transport, participant=participant)
    if form.is_valid():
        form.save()
        return redirect("fahrt:transport_chat", participant.id, transport.pk)

    context = {
        "form": form,
        "calling_participant": participant,
        "transport": transport,
    }
    return render(request, "fahrt/transportation/participant/transport_chat.html", context)


def transport_chat_by_management(request: WSGIRequest, transport_pk: int) -> HttpResponse:
    transport: Transportation = get_object_or_404(Transportation, pk=transport_pk)

    context = {
        "transport": transport,
    }
    return render(request, "fahrt/transportation/management/transport_chat.html", context)
