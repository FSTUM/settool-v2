import csv
import os
import time

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import permission_required, user_passes_test
from django.core.handlers.wsgi import WSGIRequest
from django.forms import formset_factory
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext_lazy as _

from settool_common import utils
from settool_common.models import get_semester, Semester

from .forms import (
    CompanyForm,
    CSVFileUploadForm,
    FilterCompaniesForm,
    GiveawayForm,
    ImportForm,
    MailForm,
    SelectCompanyForm,
    SelectMailForm,
    UpdateFieldForm,
)
from .models import BagMail, Company


def get_possibly_filtered_companies(filterform, semester):
    companies = semester.company_set.order_by("name")
    if filterform.is_valid():
        if filterform.cleaned_data["no_email_sent"]:
            companies = companies.filter(email_sent_success=False)
        if filterform.cleaned_data["last_year"]:
            companies = companies.filter(last_year=True)
        if filterform.cleaned_data["not_last_year"]:
            companies = companies.filter(last_year=False)
        if filterform.cleaned_data["contact_again"]:
            companies = companies.filter(contact_again=True)
        if filterform.cleaned_data["promise"]:
            companies = companies.filter(promise=True)
        if filterform.cleaned_data["no_promise"]:
            companies = companies.exclude(promise=True)
        if filterform.cleaned_data["giveaways"]:
            companies = companies.exclude(giveaways="")
        if filterform.cleaned_data["arrived"]:
            companies = companies.filter(arrived=True)
    return companies  # noqa: R504


@permission_required("bags.view_companies")
def list_companys(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    filterform = FilterCompaniesForm(request.POST or None)
    companies = get_possibly_filtered_companies(filterform, semester)

    mailform = SelectMailForm(request.POST if "mailform" in request.POST else None)
    select_company_form_set = formset_factory(SelectCompanyForm, extra=0)
    companyforms = select_company_form_set(
        request.POST if "mailform" in request.POST else None,
        initial=[{"id": c.id, "selected": True} for c in companies],
    )

    if "mailform" in request.POST and mailform.is_valid() and companyforms.is_valid():
        mail = mailform.cleaned_data["mail"]

        selected_companies = []
        for company in companyforms:
            try:
                company_id = company.cleaned_data["id"]
            except KeyError:
                continue
            try:
                selected = company.cleaned_data["selected"]
            except KeyError:
                selected = False
            if selected:
                selected_companies.append(company_id)

        request.session["selected_companies"] = selected_companies
        return redirect("bags:send_mail", mail.id)

    companies_and_select = []
    for company in companies:
        for company_form in companyforms:
            if company_form.initial["id"] == company.id:
                companies_and_select.append((company, company_form))
                break

    context = {
        "companies": companies_and_select,
        "filterform": filterform,
        "mailform": mailform,
        "companyforms": companyforms,
    }
    return render(request, "bags/bags_dashboard.html", context)


@permission_required("bags.view_companies")
def add_giveaway(request: WSGIRequest) -> HttpResponse:
    semester = get_object_or_404(Semester, pk=get_semester(request))

    form = GiveawayForm(request.POST or None, semester=semester)
    if form.is_valid():
        company = form.cleaned_data["company"]
        giveaways = form.cleaned_data["giveaways"]

        company.giveaways = giveaways
        company.save()

        return redirect("bags:add_giveaway")

    context = {
        "form": form,
    }
    return render(request, "bags/add_giveaway.html", context)


@permission_required("bags.view_companies")
def add_company(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))

    form = CompanyForm(request.POST or None, semester=semester)
    if form.is_valid():
        company = form.save()

        return redirect("bags:view_company", company.id)

    context = {"form": form}
    return render(request, "bags/company/add_company.html", context)


@permission_required("bags.view_companies")
def view_company(request: WSGIRequest, company_pk: int) -> HttpResponse:
    company = get_object_or_404(Company, pk=company_pk)

    context = {"company": company}
    return render(request, "bags/company/company_details.html", context)


@permission_required("bags.view_companies")
def edit_company(request: WSGIRequest, company_pk: int) -> HttpResponse:
    company = get_object_or_404(Company, pk=company_pk)

    form = CompanyForm(
        request.POST or None,
        semester=company.semester,
        instance=company,
    )
    if form.is_valid():
        form.save()

        return redirect("bags:view_company", company.id)

    context = {
        "form": form,
        "company": company,
    }
    return render(request, "bags/company/edit_company.html", context)


@permission_required("bags.view_companies")
def update_field(request: WSGIRequest, company_pk: int, field: str) -> HttpResponse:
    company = get_object_or_404(Company, pk=company_pk)

    form = UpdateFieldForm(request.POST or None)
    if form.is_valid():
        private_key = form.cleaned_data["pk"]
        name = form.cleaned_data["name"]
        value = form.cleaned_data["value"]
        if private_key != company.pk or name != f"company_{company.pk}_{field}":
            return HttpResponseBadRequest("")
        str_to_bool_map = {
            "True": True,
            "False": False,
            "None": None,
        }
        if value in str_to_bool_map:
            value = str_to_bool_map.get(value)
        changes = {field: value}

        # to display email_sent_success and email_sent_success in one column we use a Failure state
        # email_sent_success is apparently only a failure marker if email_sent is True
        # (email_sent_success is initialised as False)
        if field == "email_sent":
            if value == "Failure":
                changes["email_sent"] = True
                changes["email_sent_success"] = False
            else:
                changes["email_sent"] = changes["email_sent_success"] = value

        Company.objects.filter(pk=company.pk).update(**changes)
        return HttpResponse(f"#{name}")

    return HttpResponseBadRequest("")


@permission_required("bags.view_companies")
def del_company(request: WSGIRequest, company_pk: int) -> HttpResponse:
    company = get_object_or_404(Company, pk=company_pk)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        company.delete()

        return redirect("bags:dashboard")

    context = {
        "company": company,
        "form": form,
    }
    return render(request, "bags/company/del_company.html", context)


@permission_required("bags.view_companies")
def list_mails(request: WSGIRequest) -> HttpResponse:
    context = {"mails": BagMail.objects.all()}
    return render(request, "bags/mail/list_mails.html", context)


@permission_required("bags.view_companies")
def add_mail(request: WSGIRequest) -> HttpResponse:
    form = MailForm(request.POST or None)
    if form.is_valid():
        form.save()

        return redirect("bags:list_mails")

    context = {"form": form, "mail": BagMail}
    return render(request, "bags/mail/add_mail.html", context)


@permission_required("bags.view_companies")
def edit_mail(request: WSGIRequest, mail_pk: int) -> HttpResponse:
    mail = get_object_or_404(BagMail, pk=mail_pk)

    form = MailForm(request.POST or None, instance=mail)
    if form.is_valid():
        form.save()
        return redirect("bags:list_mails")

    context = {
        "form": form,
        "mail": mail,
    }
    return render(request, "bags/mail/edit_mail.html", context)


@permission_required("bags.view_companies")
def delete_mail(request: WSGIRequest, mail_pk: int) -> HttpResponse:
    mail = get_object_or_404(BagMail, pk=mail_pk)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        mail.delete()

        return redirect("bags:list_mails")

    context = {
        "mail": mail,
        "form": form,
    }
    return render(request, "bags/mail/del_mail.html", context)


@permission_required("bags.view_companies")
def send_mail(request: WSGIRequest, mail_pk: int) -> HttpResponse:
    mail = get_object_or_404(BagMail, pk=mail_pk)
    selected_companies = request.session["selected_companies"]
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    companies = semester.company_set.filter(
        id__in=selected_companies,
    ).order_by("name")

    subject, text, from_email = mail.get_mail_company()

    form = forms.Form(request.POST or None)
    if form.is_valid():
        company: Company
        for company in companies:
            company.email_sent_success = mail.send_mail_company(company)
            company.email_sent = True
            company.save()
        return redirect("bags:dashboard")

    context = {
        "companies": companies,
        "subject": subject,
        "text": text,
        "from_email": from_email,
        "form": form,
    }

    return render(request, "bags/mail/send_mail.html", context)


def import_mail_csv_to_db(csv_file, semester):
    # load content into tempfile
    tmp_filename = f"upload_{csv_file.name}"
    with open(tmp_filename, "wb+") as tmp_csv_file:
        for chunk in csv_file.chunks():
            tmp_csv_file.write(chunk)
    # create new mail
    with open(tmp_filename, "r") as tmp_csv_file:
        rows = csv.DictReader(tmp_csv_file)
        for row in rows:
            Company.objects.update_or_create(
                semester=semester,
                name=row["name"],
                defaults={
                    "contact_firstname": row["contact_firstname"],
                    "contact_lastname": row["contact_lastname"],
                    "email": row["email"],
                    "contact_gender": row["contact_gender"],
                    "email_sent": row["email_sent"],
                    "email_sent_success": row["email_sent_success"],
                    "promise": row["promise"],
                    "giveaways": row["giveaways"],
                    "giveaways_last_year": row["giveaways_last_year"],
                    "arrival_time": row["arrival_time"],
                    "comment": row["comment"],
                    "last_year": row["last_year"],
                    "arrived": row["arrived"],
                    "contact_again": row["contact_again"],
                },
            )
    # delete tempfile
    os.remove(tmp_filename)


@user_passes_test(lambda user: user.is_staff)
@permission_required("bags.view_companies")
def import_csv(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    file_upload_form = CSVFileUploadForm(request.POST or None, request.FILES)
    if file_upload_form.is_valid():
        import_mail_csv_to_db(request.FILES["file"], semester)
        messages.success(request, _("The File was successfully uploaded"))
        return redirect("bags:main_index")
    return render(
        request,
        "bags/import-export/import_csv.html",
        {"form": file_upload_form},
    )


@permission_required("bags.view_companies")
@user_passes_test(lambda user: user.is_staff)
def import_previous_semester(request: WSGIRequest) -> HttpResponse:
    new_semester: Semester = get_object_or_404(Semester, pk=get_semester(request))

    form = ImportForm(request.POST or None, semester=new_semester)
    if form.is_valid():
        old_semester = form.cleaned_data["semester"]
        only_contact_again = form.cleaned_data["only_contact_again"]

        companies = old_semester.company_set.exclude(contact_again=False)
        if only_contact_again:
            companies = old_semester.company_set.filter(contact_again=True)

        for company in companies:
            # do not import company when it already exists
            if new_semester.company_set.filter(name=company.name).exists():
                continue

            Company.objects.create(
                semester=new_semester,
                name=company.name,
                contact_gender=company.contact_gender,
                contact_firstname=company.contact_firstname,
                contact_lastname=company.contact_lastname,
                email=company.email,
                email_sent=False,
                email_sent_success=False,
                promise=None,
                giveaways="",
                giveaways_last_year=company.giveaways,
                arrival_time="",
                comment="",
                last_year=True,
                arrived=False,
                contact_again=None,
            )
        return redirect("bags:dashboard")

    context = {
        "form": form,
    }

    return render(request, "bags/import-export/import_companies.html", context)


@permission_required("guidedtours.view_participants")
def export_csv(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    companies = semester.company_set.order_by("name")
    return utils.download_csv(
        [
            "name",
            "contact_gender",
            "contact_firstname",
            "contact_lastname",
            "email",
            "email_sent",
            "email_sent_success",
            "promise",
            "giveaways",
            "giveaways_last_year",
            "arrival_time",
            "comment",
            "last_year",
            "arrived",
            "contact_again",
        ],
        f"companies_{time.strftime('%Y%m%d-%H%M')}.csv",
        companies,
    )
