from django import forms
from django.contrib.auth.decorators import permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from settool_common.models import get_semester, Semester

from ..forms import FahrtForm, MailForm
from ..models import Fahrt, FahrtMail


@permission_required("fahrt.view_participants")
def list_mails(request: WSGIRequest) -> HttpResponse:
    context = {"mails": FahrtMail.objects.all()}
    return render(request, "fahrt/maintinance/mail/list_mails.html", context)


@permission_required("fahrt.view_participants")
def add_mail(request: WSGIRequest) -> HttpResponse:
    form = MailForm(request.POST or None)
    if form.is_valid():
        form.save()

        return redirect("fahrt:list_mails")

    context = {"form": form, "mail": FahrtMail}
    return render(request, "fahrt/maintinance/mail/add_mail.html", context)


@permission_required("fahrt.view_participants")
def edit_mail(request: WSGIRequest, mail_pk: int) -> HttpResponse:
    mail = get_object_or_404(FahrtMail, pk=mail_pk)

    form = MailForm(request.POST or None, instance=mail)
    if form.is_valid():
        form.save()

        return redirect("fahrt:list_mails")

    context = {
        "form": form,
        "mail": mail,
    }
    return render(request, "fahrt/maintinance/mail/edit_mail.html", context)


@permission_required("fahrt.view_participants")
def del_mail(request: WSGIRequest, mail_pk: int) -> HttpResponse:
    mail = get_object_or_404(FahrtMail, pk=mail_pk)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        mail.delete()

        return redirect("fahrt:list_mails")

    context = {
        "mail": mail,
        "form": form,
    }
    return render(request, "fahrt/maintinance/mail/del_mail.html", context)


@permission_required("fahrt.view_participants")
def send_mail(request: WSGIRequest, mail_pk: int) -> HttpResponse:
    mail: FahrtMail = get_object_or_404(FahrtMail, pk=mail_pk)
    selected_participants = request.session["selected_participants"]
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
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
            return redirect("fahrt:filter")

    context = {
        "participants": participants,
        "failed_participants": failed_participants,
        "subject": subject,
        "text": text,
        "from_email": from_email,
        "form": form,
    }

    if failed_participants:
        return render(request, "fahrt/maintinance/mail/send_mail_failure.html", context)
    return render(request, "fahrt/maintinance/mail/send_mail.html", context)


@permission_required("fahrt.view_participants")
def settings(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))

    fahrt: Fahrt = Fahrt.objects.get_or_create(
        semester=semester,
        defaults={
            "date": timezone.now().date(),
            "open_registration": timezone.now(),
            "close_registration": timezone.now(),
        },
    )[0]

    form = FahrtForm(request.POST or None, instance=fahrt)
    if form.is_valid():
        form.save()
        return redirect("fahrt:main_index")

    context = {
        "form": form,
    }
    return render(request, "fahrt/maintinance/settings.html", context)
