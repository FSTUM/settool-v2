import csv
import os
import time
from typing import Any, Dict, Optional, Tuple

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Count, QuerySet
from django.forms import forms
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import is_safe_url
from django.utils.translation import ugettext_lazy as _

import fahrt
import guidedtours
import tutors
from bags.models import BagMail
from fahrt.models import FahrtMail
from guidedtours.models import TourMail
from settool_common import utils
from settool_common.forms import MailForm
from settool_common.models import get_semester, Mail, Semester
from tutors.models import TutorMail

from .forms import CSVFileUploadForm
from .settings import SEMESTER_SESSION_KEY


@login_required
def set_semester(request: WSGIRequest) -> HttpResponse:
    redirect_url: Optional[str] = request.POST.get("next") or request.GET.get("next")
    if not is_safe_url(url=redirect_url, allowed_hosts=request.get_host()):
        redirect_url = request.META.get("HTTP_REFERER")
        if not is_safe_url(url=redirect_url, allowed_hosts=request.get_host()):
            redirect_url = "/"  # should not happen :)
    if request.method == "POST":
        semester_pk = int(request.POST.get("semester") or -1)  # semester is always present
        try:
            Semester.objects.get(pk=semester_pk)
        except Semester.DoesNotExist:
            pass
        else:
            request.session[SEMESTER_SESSION_KEY] = semester_pk
    return HttpResponseRedirect(redirect_url or "/")


@permission_required("set.mail")
def mail_list(request: WSGIRequest) -> HttpResponse:
    context = {"mails": Mail.objects.all()}
    return render(request, "settool_common/settings/mail/list_email_templates.html", context)


@permission_required("set.mail")
def filtered_mail_list(request: WSGIRequest, mail_filter: str) -> HttpResponse:
    mail_lut: Dict[str, Tuple[QuerySet[Any], str]] = {
        # "bags": (BagMail.objects.all(), "bags.view_companies"),
        # "fahrt": (FahrtMail.objects.all(), "fahrt.view_participants"),
        # "guidedtours": (TourMail.objects.all(), "guidedtours.view_participants"),
        "tutors": (TutorMail.objects.all(), "set.mail"),
    }
    if mail_filter not in mail_lut.keys():
        raise Http404
    mail_qs, _ = mail_lut[mail_filter]
    # if not request.user.has_perm(mail_object["required_perm"]):
    #    return redirect("main-view")
    context = {"mails": mail_qs, "mail_filter": mail_filter}
    return render(request, "settool_common/settings/mail/list_email_templates.html", context)


@permission_required("set.mail")
def mail_view(request: WSGIRequest, mail_pk: int) -> HttpResponse:
    mail = Mail.objects.get(pk=mail_pk)

    context = {
        "mail": mail,
    }
    return render(request, "settool_common/settings/mail/email_details.html", context)


@permission_required("set.mail")
def mail_add(request: WSGIRequest) -> HttpResponse:
    form = MailForm(request.POST or None, user=request.user)
    if form.is_valid():
        form.save()
        return redirect("mail_list")

    context = {
        "form": form,
        "mails": form.get_mails().items(),
    }
    return render(request, "settool_common/settings/mail/add_email.html", context)


@permission_required("set.mail")
def mail_edit(request: WSGIRequest, mail_pk: int) -> HttpResponse:
    mail = get_object_or_404(Mail, pk=mail_pk)

    form = MailForm(request.POST or None, instance=mail, user=request.user)
    if form.is_valid():
        form.save()
        return redirect("mail_list")

    context = {
        "form": form,
        "mail": mail,
        "mails": form.get_mails().items(),
    }
    return render(request, "settool_common/settings/mail/edit_email.html", context)


@permission_required("set.mail")
def mail_delete(request: WSGIRequest, mail_pk: int) -> HttpResponse:
    mail = get_object_or_404(Mail, pk=mail_pk)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        mail.delete()
        return redirect("mail_list")

    context = {
        "mail": mail,
        "form": form,
    }
    return render(request, "settool_common/settings/mail/delete_email.html", context)


def object_does_exists(klass: Any, semester: Semester) -> bool:
    try:
        klass.objects.get(semester=semester)
    except ObjectDoesNotExist:
        return False
    return True


@permission_required("set.mail")
def dashboard(request: WSGIRequest) -> HttpResponse:
    semester = get_object_or_404(Semester, pk=get_semester(request))
    mail_templates_by_sender = (
        Mail.objects.values("sender").annotate(sender_count=Count("sender")).order_by("-sender_count")
    )
    context = {
        "mail_template_sender": [sender["sender"] for sender in mail_templates_by_sender],
        "mail_template_count": [sender["sender_count"] for sender in mail_templates_by_sender],
        "fahrt_exists": object_does_exists(fahrt.models.Fahrt, semester),
        "tutor_general_exists": object_does_exists(tutors.models.Settings, semester),
        "guidedtours_exists": object_does_exists(guidedtours.models.Setting, semester),
    }
    return render(request, "settool_common/settings/settings_dashboard.html", context)


def import_mail_csv_to_db(csv_file):
    # load content into tempfile
    tmp_filename = f"upload_{csv_file.name}"
    with open(tmp_filename, "wb+") as tmp_csv_file:
        for chunk in csv_file.chunks():
            tmp_csv_file.write(chunk)
    # delete all mail
    BagMail.objects.all().delete()
    FahrtMail.objects.all().delete()
    TourMail.objects.all().delete()
    Mail.objects.all().delete()
    TutorMail.objects.all().delete()
    # create new mail
    with open(tmp_filename, "r") as tmp_csv_file:
        rows = csv.DictReader(tmp_csv_file)
        for row in rows:
            Mail.objects.create(
                sender=row["sender"],
                subject=row["subject"],
                text=row["text"],
                comment=row["comment"],
            )
    # delete tempfile
    os.remove(tmp_filename)


@user_passes_test(lambda u: u.is_superuser)
@permission_required("set.mail")
def mail_import(request: WSGIRequest) -> HttpResponse:
    file_upload_form = CSVFileUploadForm(request.POST or None, request.FILES)
    if file_upload_form.is_valid():
        import_mail_csv_to_db(request.FILES["file"])
        messages.success(request, _("The File was successfully uploaded"))
        return redirect("mail_list")
    return render(
        request,
        "settool_common/settings/mail/import_email.html",
        {"form": file_upload_form},
    )


@permission_required("set.mail")
def mail_export(request: WSGIRequest) -> HttpResponse:
    mails_bags = BagMail.objects.all()
    mails_fahrt = FahrtMail.objects.all()
    mails_guidedtours = TourMail.objects.all()
    mails_settool_common = Mail.objects.all()

    mails = [_clean_mail(mail) for mail in mails_bags]
    mails += [_clean_mail(mail) for mail in mails_fahrt]
    mails += [_clean_mail(mail) for mail in mails_guidedtours]
    mails += [_clean_mail(mail) for mail in mails_settool_common]

    filename = f"emails{time.strftime('%Y%m%d-%H%M')}.csv"
    return utils.download_csv(["sender", "subject", "text", "comment"], filename, mails)


def _clean_mail(mail):
    return {
        "sender": mail.sender or "",
        "subject": mail.subject or "",
        "text": mail.text or "",
        "comment": mail.comment if hasattr(mail, "comment") else "",
    }
