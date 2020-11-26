from django import forms
from django.contrib.auth.decorators import permission_required, \
    user_passes_test
from django.forms import formset_factory
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404, redirect

from settool_common.models import get_semester, Semester
from .forms import CompanyForm, MailForm, SelectMailForm, \
    FilterCompaniesForm, SelectCompanyForm, GiveawayForm, ImportForm, \
    UpdateFieldForm
from .models import Company, Mail


@permission_required('bags.view_companies')
def index(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    companies = semester.company_set.order_by("name")

    filterform = FilterCompaniesForm(request.POST or None)
    if filterform.is_valid():
        if filterform.cleaned_data['no_email_sent']:
            companies = companies.filter(email_sent_success=False)
        if filterform.cleaned_data['last_year']:
            companies = companies.filter(last_year=True)
        if filterform.cleaned_data['not_last_year']:
            companies = companies.filter(last_year=False)
        if filterform.cleaned_data['contact_again']:
            companies = companies.filter(contact_again=True)
        if filterform.cleaned_data['promise']:
            companies = companies.filter(promise=True)
        if filterform.cleaned_data['no_promise']:
            companies = companies.exclude(promise=True)
        if filterform.cleaned_data['giveaways']:
            companies = companies.exclude(giveaways="")
        if filterform.cleaned_data['arrived']:
            companies = companies.filter(arrived=True)

    if "mailform" in request.POST:
        mailform = SelectMailForm(request.POST, semester=semester)
        select_company_form_set = formset_factory(SelectCompanyForm, extra=0)
        companyforms = select_company_form_set(request.POST,
                                               initial=[{'id': c.id, 'selected': True} for c in companies],
                                               )
    else:
        mailform = SelectMailForm(None, semester=semester)
        select_company_form_set = formset_factory(SelectCompanyForm, extra=0)
        companyforms = select_company_form_set(None,
                                               initial=[{'id': c.id, 'selected': True} for c in companies],
                                               )

    if "mailform" in request.POST and mailform.is_valid() and \
            companyforms.is_valid():
        mail = mailform.cleaned_data['mail']

        selected_companies = []
        for i, company in enumerate(companyforms):
            try:
                company_id = company.cleaned_data['id']
            except KeyError:
                continue
            try:
                selected = company.cleaned_data['selected']
            except KeyError:
                selected = False
            if selected:
                selected_companies.append(company_id)

        request.session['selected_companies'] = selected_companies
        return redirect('sendmail', mail.id)

    companies_and_select = []
    for c in companies:
        for s in companyforms:
            if s.initial['id'] == c.id:
                companies_and_select.append((c, s))
                break

    context = {
        'companies': companies_and_select,
        'filterform': filterform,
        'mailform': mailform,
        'companyforms': companyforms,
    }
    return render(request, 'bags/index.html', context)


@permission_required('bags.view_companies')
def insert_giveaways(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)

    form = GiveawayForm(request.POST or None, semester=semester)
    if form.is_valid():
        company = form.cleaned_data['company']
        giveaways = form.cleaned_data['giveaways']

        company.giveaways = giveaways
        company.save()

        return redirect('insert_giveaways')

    context = {
        'form': form,
    }
    return render(request, 'bags/insert_giveaways.html', context)


@permission_required('bags.view_companies')
def add(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)

    form = CompanyForm(request.POST or None, semester=semester)
    if form.is_valid():
        company = form.save()

        return redirect('viewcompany', company.id)

    context = {'form': form}
    return render(request, 'bags/add_company.html', context)


@permission_required('bags.view_companies')
def view(request, company_pk):
    company = get_object_or_404(Company, pk=company_pk)

    context = {'company': company}
    return render(request, 'bags/view.html', context)


@permission_required('bags.view_companies')
def edit(request, company_pk):
    company = get_object_or_404(Company, pk=company_pk)

    form = CompanyForm(request.POST or None, semester=company.semester,
                       instance=company)
    if form.is_valid():
        form.save()

        return redirect('viewcompany', company.id)

    context = {'form': form,
               'company': company}
    return render(request, 'bags/edit_company.html', context)


@permission_required('bags.view_companies')
def update_field(request, company_pk, field):
    company = get_object_or_404(Company, pk=company_pk)

    form = UpdateFieldForm(request.POST or None)
    if form.is_valid():
        pk = form.cleaned_data['pk']
        name = form.cleaned_data['name']
        value = form.cleaned_data['value']

        if pk != company.pk or \
                name != "company_{}_{}".format(company.pk, field):
            return HttpResponseBadRequest('')

        changes = {field: value}
        Company.objects.filter(pk=company.pk).update(**changes)
        return HttpResponse('')

    return HttpResponseBadRequest('')


@permission_required('bags.view_companies')
def delete(request, company_pk):
    company = get_object_or_404(Company, pk=company_pk)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        company.delete()

        return redirect('listcompanies')

    context = {'company': company,
               'form': form}
    return render(request, 'bags/del_company.html', context)


@permission_required('bags.view_companies')
def index_mails(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    mails = semester.mail_set.all()

    context = {'mails': mails}
    return render(request, 'bags/index_mails.html', context)


@permission_required('bags.view_companies')
def add_mail(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)

    form = MailForm(request.POST or None, semester=semester)
    if form.is_valid():
        form.save()

        return redirect('listmails')

    context = {'form': form}
    return render(request, 'bags/add_mail.html', context)


@permission_required('bags.view_companies')
def edit_mail(request, mail_pk):
    mail = get_object_or_404(Mail, pk=mail_pk)

    form = MailForm(request.POST or None, semester=mail.semester,
                    instance=mail)
    if form.is_valid():
        form.save()

        return redirect('listmails')

    context = {'form': form,
               'mail': mail}
    return render(request, 'bags/edit_mail.html', context)


@permission_required('bags.view_companies')
def delete_mail(request, mail_pk):
    mail = get_object_or_404(Mail, pk=mail_pk)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        mail.delete()

        return redirect('listmails')

    context = {'mail': mail,
               'form': form}
    return render(request, 'bags/del_mail.html', context)


@permission_required('bags.view_companies')
def send_mail(request, mail_pk):
    mail = get_object_or_404(Mail, pk=mail_pk)
    selected_companies = request.session['selected_companies']
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    companies = semester.company_set.filter(id__in=selected_companies
                                            ).order_by("name")

    subject, text, from_email = mail.get_mail()

    form = forms.Form(request.POST or None)
    if form.is_valid():
        for c in companies:
            mail.send_mail(c)
            semester.company_set.filter(id=c.id).update(
                email_sent=True,
                email_sent_success=True,
            )
        return redirect('listcompanies')

    context = {
        'companies': companies,
        'subject': subject,
        'text': text,
        'from_email': from_email,
        'form': form,
    }

    return render(request, 'bags/send_mail.html', context)


@user_passes_test(lambda u: u.is_staff)
def import_companies(request):
    sem = get_semester(request)
    new_semester = get_object_or_404(Semester, pk=sem)

    form = ImportForm(request.POST or None, semester=new_semester)
    if form.is_valid():
        old_semester = form.cleaned_data['semester']
        only_contact_again = form.cleaned_data['only_contact_again']

        companies = old_semester.company_set.exclude(contact_again=False)
        if only_contact_again:
            companies = old_semester.company_set.filter(contact_again=True)

        for c in companies:
            # do not import company when it already exists
            if new_semester.company_set.filter(name=c.name).exists():
                continue

            Company.objects.create(
                semester=new_semester,
                name=c.name,
                contact_gender=c.contact_gender,
                contact_firstname=c.contact_firstname,
                contact_lastname=c.contact_lastname,
                email=c.email,
                email_sent=False,
                email_sent_success=False,
                promise=None,
                giveaways="",
                giveaways_last_year=c.giveaways,
                arrival_time="",
                comment="",
                last_year=True,
                arrived=False,
                contact_again=None,
            )
        return redirect("listcompanies")

    context = {
        'form': form,
    }

    return render(request, 'bags/import_companies.html', context)
