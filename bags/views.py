from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import permission_required

from settool_common.models import get_semester, Semester
from .forms import CompanyForm
from .models import Company

@permission_required('bags.view_companies')
def index(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    companies = semester.company_set.order_by("name")

    context = {'companies': companies}
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
def delete(request):
    pass


@permission_required('bags.view_companies')
def index_mails(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    mails = semester.mail_set.all()

    context = {'mails': mails}
    return render(request, 'bags/index_mails.html', context)


@permission_required('bags.view_companies')
def add_mail(request):
    pass


@permission_required('bags.view_companies')
def edit_mail(request):
    pass


@permission_required('bags.view_companies')
def delete_mail(request):
    pass
