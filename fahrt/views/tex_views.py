import time
from typing import Union

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django_tex.response import PDFResponse
from django_tex.shortcuts import render_to_pdf

from settool_common import utils
from settool_common.models import get_semester, Semester

from ..models import Fahrt, Participant


@permission_required("fahrt.view_participants")
def export(request: WSGIRequest, file_format: str = "csv") -> Union[HttpResponse, PDFResponse]:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    try:
        fahrt = semester.fahrt
    except ObjectDoesNotExist:
        messages.error(request, _("Please setup the SETtings for the Fahrt"))
        return redirect("fahrt:settings")
    participants = Participant.objects.filter(semester=semester).order_by("surname", "firstname")
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
    return render_to_pdf(request, "fahrt/tex/participants.tex", context, f"{filename}.pdf")


@permission_required("fahrt.view_participants")
def non_liability_form(request: WSGIRequest, participant_pk: int) -> PDFResponse:
    return get_non_liability(request, participant_pk)


def get_non_liability(request: WSGIRequest, participant_pk: int) -> PDFResponse:
    participant: Participant = get_object_or_404(Participant, pk=participant_pk)
    fahrt: Fahrt = get_object_or_404(Fahrt, semester=participant.semester)
    context = {
        "participant": participant,
        "fahrt": fahrt,
    }
    filename = f"non_liability_{participant.surname}_{participant.firstname}.pdf"
    if participant.u18:
        return render_to_pdf(request, "fahrt/tex/u18_non_liability.tex", context, filename)
    return render_to_pdf(request, "fahrt/tex/ü18_non_liability.tex", context, filename)
