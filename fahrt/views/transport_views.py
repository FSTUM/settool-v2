from typing import Any, List, Optional, Tuple
from uuid import UUID

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext_lazy as _

from settool_common.models import get_semester, Semester

from ..forms import (
    AddParticipantToTransportForm,
    ParticipantSelectForm,
    TransportAdminOptionForm,
    TransportationCommentForm,
    TransportOptionForm,
)
from ..models import Fahrt, Participant, Transportation


def get_transport_types(fahrt: Fahrt) -> List[Tuple[str, str, Any]]:
    return [
        (_("Cars"), _("Car"), Transportation.objects.filter(transport_type=Transportation.CAR, fahrt=fahrt)),
        (_("Trains"), _("Train"), Transportation.objects.filter(transport_type=Transportation.TRAIN, fahrt=fahrt)),
    ]


def transport_participant(request: WSGIRequest, participant_uuid: UUID) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    participant: Participant = get_object_or_404(Participant, uuid=participant_uuid, status="confirmed")
    context = {
        "transport_types": get_transport_types(semester.fahrt),
        "calling_participant": participant,
    }
    return render(request, "fahrt/transportation/list_transports.html", context)


def add_transport_option(request: WSGIRequest, participant_uuid: UUID, transport_type: int) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    participant: Participant = get_object_or_404(Participant, uuid=participant_uuid, status="confirmed")
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
        semester=semester,
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
    return render(request, "fahrt/transportation/add_transport.html", context)


def add_transport_participant(request: WSGIRequest, participant_uuid: UUID, transport_pk: int) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    participant: Participant = get_object_or_404(Participant, uuid=participant_uuid, status="confirmed")
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
    context = {"transport_types": get_transport_types(semester.fahrt)}
    return render(
        request,
        "fahrt/transportation/list_transports.html",
        context,
    )


@permission_required("fahrt.view_participants")
def add_transport_option_by_management(request: WSGIRequest, transport_type: int) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    if transport_type not in [Transportation.CAR, Transportation.TRAIN]:
        raise Http404()

    form = TransportAdminOptionForm(request.POST or None, transport_type=transport_type, semester=semester)
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
    return render(request, "fahrt/transportation/add_transport.html", context)


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
    participant: Participant = get_object_or_404(Participant, uuid=participant_uuid, status="confirmed")
    transport: Optional[Transportation] = participant.transportation

    form = ParticipantSelectForm(request.POST or None, semester=semester)
    if form.is_valid():
        participant2: Participant = form.cleaned_data["selected"]
        if participant2 == participant:
            messages.warning(request, _("Succesfully exchanged {p1} with itsself :)").format(p1=participant))
            return redirect("fahrt:transport_mangagement")

        # possibly exchanging creators
        if participant.transportation and participant.transportation.creator == participant:
            participant.transportation.creator = participant2
            participant.transportation.save()
        if participant2.transportation and participant2.transportation.creator == participant2:
            participant2.transportation.creator = participant
            participant2.transportation.save()
        # possibly exchanging transportation
        participant.transportation = participant2.transportation
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
    participant: Participant = get_object_or_404(Participant, uuid=participant_uuid, status="confirmed")
    transport: Optional[Transportation] = participant.transportation
    if transport is None:
        messages.warning(
            request,
            _(
                "This participant is not assigned to a transport option. this can Thus not be edited. You can however "
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
    participant: Participant = get_object_or_404(Participant, uuid=participant_uuid, status="confirmed")
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
        return redirect("fahrt:transport_chat", participant.uuid, transport.pk)

    context = {
        "form": form,
        "calling_participant": participant,
        "transport": transport,
    }
    return render(request, "fahrt/transportation/transport_chat.html", context)


def transport_chat_by_management(request: WSGIRequest, transport_pk: int) -> HttpResponse:
    transport: Transportation = get_object_or_404(Transportation, pk=transport_pk)

    context = {
        "transport": transport,
    }
    return render(request, "fahrt/transportation/transport_chat.html", context)