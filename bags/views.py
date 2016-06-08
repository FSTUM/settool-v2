from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import permission_required
from django import forms

from settool_common.models import get_semester, Semester
from .forms import CompanyForm, MailForm, SelectMailForm
from .models import Company, Mail

@permission_required('bags.view_companies')
def index(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    companies = semester.company_set.order_by("name")

    form = SelectMailForm(request.POST or None, semester=semester)
    if form.is_valid():
        mail = form.cleaned_data['mail']
        company = form.cleaned_data['company'] # TODO: not implemented yet

        mail.send_mail(request, company)

        return redirect('listcompanies')

    context = {
        'companies': companies,
        'form': form
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
