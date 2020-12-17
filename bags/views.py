from django import forms
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.decorators import user_passes_test
from django.forms import formset_factory
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render

from settool_common.models import get_semester
from settool_common.models import Semester

from .forms import CompanyForm
from .forms import FilterCompaniesForm
from .forms import GiveawayForm
from .forms import ImportForm
from .forms import MailForm
from .forms import SelectCompanyForm
from .forms import SelectMailForm
from .forms import UpdateFieldForm
from .models import Company
from .models import Mail


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
def bags_dashboard(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    filterform = FilterCompaniesForm(request.POST or None)
    companies = get_possibly_filtered_companies(filterform, semester)

    if "mailform" in request.POST:
        mailform = SelectMailForm(request.POST, semester=semester)
        select_company_form_set = formset_factory(SelectCompanyForm, extra=0)
        companyforms = select_company_form_set(
            request.POST,
            initial=[{"id": c.id, "selected": True} for c in companies],
        )
    else:
        mailform = SelectMailForm(None, semester=semester)
        select_company_form_set = formset_factory(SelectCompanyForm, extra=0)
        companyforms = select_company_form_set(
            None,
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
        return redirect("sendmail", mail.id)

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
def insert_giveaways(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)

    form = GiveawayForm(request.POST or None, semester=semester)
    if form.is_valid():
        company = form.cleaned_data["company"]
        giveaways = form.cleaned_data["giveaways"]

        company.giveaways = giveaways
        company.save()

        return redirect("insert_giveaways")

    context = {
        "form": form,
    }
    return render(request, "bags/insert_giveaways.html", context)


@permission_required("bags.view_companies")
def add(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)

    form = CompanyForm(request.POST or None, semester=semester)
    if form.is_valid():
        company = form.save()

        return redirect("viewcompany", company.id)

    context = {"form": form}
    return render(request, "bags/add_company.html", context)


@permission_required("bags.view_companies")
def view(request, company_pk):
    company = get_object_or_404(Company, pk=company_pk)

    context = {"company": company}
    return render(request, "bags/view.html", context)


@permission_required("bags.view_companies")
def edit(request, company_pk):
    company = get_object_or_404(Company, pk=company_pk)

    form = CompanyForm(
        request.POST or None,
        semester=company.semester,
        instance=company,
    )
    if form.is_valid():
        form.save()

        return redirect("viewcompany", company.id)

    context = {
        "form": form,
        "company": company,
    }
    return render(request, "bags/edit_company.html", context)


@permission_required("bags.view_companies")
def update_field(request, company_pk, field):
    company = get_object_or_404(Company, pk=company_pk)

    form = UpdateFieldForm(request.POST or None)
    if form.is_valid():
        private_key = form.cleaned_data["pk"]
        name = form.cleaned_data["name"]
        value = form.cleaned_data["value"]
        str_to_bool_map = {
            "True": True,
            "False": False,
            "None": None,
        }
        if value in str_to_bool_map.keys():
            value = str_to_bool_map[value]
        if private_key != company.pk or name != f"company_{company.pk}_{field}":
            return HttpResponseBadRequest("")

        changes = {field: value}
        Company.objects.filter(pk=company.pk).update(**changes)
        return HttpResponse("")

    return HttpResponseBadRequest("")


@permission_required("bags.view_companies")
def delete(request, company_pk):
    company = get_object_or_404(Company, pk=company_pk)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        company.delete()

        return redirect("bags_dashboard")

    context = {
        "company": company,
        "form": form,
    }
    return render(request, "bags/del_company.html", context)


@permission_required("bags.view_companies")
def index_mails(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    mails = semester.mail_set.all()

    context = {"mails": mails}
    return render(request, "bags/index_mails.html", context)


@permission_required("bags.view_companies")
def add_mail(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)

    form = MailForm(request.POST or None, semester=semester)
    if form.is_valid():
        form.save()

        return redirect("listmails")

    context = {"form": form}
    return render(request, "bags/add_mail.html", context)


@permission_required("bags.view_companies")
def edit_mail(request, mail_pk):
    mail = get_object_or_404(Mail, pk=mail_pk)

    form = MailForm(
        request.POST or None,
        semester=mail.semester,
        instance=mail,
    )
    if form.is_valid():
        form.save()

        return redirect("listmails")

    context = {
        "form": form,
        "mail": mail,
    }
    return render(request, "bags/edit_mail.html", context)


@permission_required("bags.view_companies")
def delete_mail(request, mail_pk):
    mail = get_object_or_404(Mail, pk=mail_pk)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        mail.delete()

        return redirect("listmails")

    context = {
        "mail": mail,
        "form": form,
    }
    return render(request, "bags/del_mail.html", context)


@permission_required("bags.view_companies")
def send_mail(request, mail_pk):
    mail = get_object_or_404(Mail, pk=mail_pk)
    selected_companies = request.session["selected_companies"]
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    companies = semester.company_set.filter(
        id__in=selected_companies,
    ).order_by("name")

    subject, text, from_email = mail.get_mail()

    form = forms.Form(request.POST or None)
    if form.is_valid():
        for company in companies:
            mail.send_mail(company)
            semester.company_set.filter(id=company.id).update(
                email_sent=True,
                email_sent_success=True,
            )
        return redirect("bags_dashboard")

    context = {
        "companies": companies,
        "subject": subject,
        "text": text,
        "from_email": from_email,
        "form": form,
    }

    return render(request, "bags/send_mail.html", context)


@user_passes_test(lambda u: u.is_staff)
def import_companies(request):
    sem = get_semester(request)
    new_semester = get_object_or_404(Semester, pk=sem)

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
        return redirect("bags_dashboard")

    context = {
        "form": form,
    }

    return render(request, "bags/import_companies.html", context)
