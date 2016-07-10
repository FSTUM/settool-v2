from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import permission_required
from django import forms
from django.db.models import Q
from django.forms import formset_factory

from settool_common.models import get_semester, Semester
from .forms import CompanyForm, MailForm, SelectMailForm, \
    FilterCompaniesForm, SelectCompanyForm
from .models import Company, Mail

@permission_required('bags.view_companies')
def index(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    companies = semester.company_set.order_by("name")


    filterform = FilterCompaniesForm(request.POST or None)

    if filterform.is_valid():
        search = filterform.cleaned_data['search']
        no_email_sent = filterform.cleaned_data['no_email_sent']
        arrived = filterform.cleaned_data['arrived']
        last_year = filterform.cleaned_data['last_year']
        not_last_year = filterform.cleaned_data['not_last_year']
        contact_again = filterform.cleaned_data['contact_again']

        if search:
            companies = companies.filter(
                Q(name__icontains=search) |
                Q(contact_gender__icontains=search) |
                Q(contact_firstname__icontains=search) |
                Q(contact_lastname__icontains=search) |
                Q(email__icontains=search) |
                Q(giveaways__icontains=search) |
                Q(arrival_time__icontains=search) |
                Q(comment__icontains=search)
            )
        if no_email_sent:
            companies = companies.filter(email_sent_success=False)
        if arrived:
            companies = companies.filter(arrived=True)
        if last_year:
            companies = companies.filter(last_year=True)
        if not_last_year:
            companies = companies.filter(last_year=False)
        if contact_again:
            companies = companies.filter(contact_again=True)

        filtered_companies = [c.id for c in companies]
        request.session['filtered_companies'] = filtered_companies
        return redirect('filteredcompanies')

    context = {
        'companies': companies,
        'filterform': filterform,
    }
    return render(request, 'bags/index.html', context)


@permission_required('bags.view_companies')
def filtered_index(request):
    filtered_companies = request.session['filtered_companies']
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    companies = semester.company_set.filter(id__in=filtered_companies
        ).order_by("name")

    form = SelectMailForm(request.POST or None, semester=semester)
    SelectCompanyFormSet = formset_factory(SelectCompanyForm, extra=0)
    companyforms = SelectCompanyFormSet(request.POST or None,
        initial=[{'id': c.id, 'selected': True} for c in companies],
    )

    if form.is_valid() and companyforms.is_valid():
        mail = form.cleaned_data['mail']

        selected_companies = []
        for i, company in enumerate(companyforms):
            try:
                company_id = company.cleaned_data['id']
            except KeyError:
                print(i, "no id")
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
        'form': form,
        'companyforms': companyforms,
    }
    return render(request, 'bags/filtered_index.html', context)


@permission_required('bags.view_companies')
def add(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)

    form = CompanyForm(request.POST or None, semester=semester)
    if form.is_valid():
        company = form.save()

        return redirect('viewcompany', company.id)

    context = {'form': form}
    return render(request, 'bags/add.html', context)


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
    return render(request, 'bags/edit.html', context)


@permission_required('bags.view_companies')
def delete(request, company_pk):
    company = get_object_or_404(Company, pk=company_pk)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        company.delete()

        return redirect('listcompanies')

    context = {'company': company,
               'form': form}
    return render(request, 'bags/del.html', context)


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

    subject, text, from_email = mail.get_mail(request)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        for c in companies:
            mail.send_mail(request, c)
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

