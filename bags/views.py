from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import permission_required
from django import forms
from django.db.models import Q

from settool_common.models import get_semester, Semester
from .forms import CompanyForm, MailForm, SelectMailForm, FilterCompaniesForm
from .models import Company, Mail

@permission_required('bags.view_companies')
def index(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    companies = semester.company_set.order_by("name")

    if request.method == 'POST':
        if 'mailform' in request.POST:
            form = SelectMailForm(request.POST, semester=semester)
            filterform = FilterCompaniesForm()
            if form.is_valid():
                mail = form.cleaned_data['mail']

                for company in companies:
                    mail.send_mail(request, company)

                return redirect('listcompanies')
        elif 'filterform' in request.POST:
            filterform = FilterCompaniesForm(request.POST)
            form = SelectMailForm(semester=semester)
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
    else:
        form = SelectMailForm(semester=semester)
        filterform = FilterCompaniesForm()

    context = {
        'companies': companies,
        'form': form,
        'filterform': filterform
    }
    return render(request, 'bags/index.html', context)


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
def send_mail(request, company_pk, mail_pk):
    # TODO
    return redirect('listcompanies')
