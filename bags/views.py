from django.shortcuts import render, get_object_or_404, redirect


from settool_common.models import get_semester, Semester
from .forms import CompanyForm

def index(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    companies = semester.company_set.order_by("name")

    context = {'companies': companies}
    return render(request, 'bags/index.html', context)


def add(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)

    form = CompanyForm(request.POST or None, semester=semester)
    if form.is_valid():
        form.save()

        return redirect('addcompany')

    context = {'form': form}
    return render(request, 'bags/add.html', context)


def view(request):
    pass


def edit(request):
    pass


def delete(request):
    pass
