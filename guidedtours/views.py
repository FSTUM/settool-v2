from django.shortcuts import render, get_object_or_404

from .models import Tour

def index(request):
    tours = Tour.objects.order_by('date')

    context = {'tours': tours}
    return render(request, 'guidedtours/index.html', context)


def view(request, tour_pk):
    tour = get_object_or_404(Tour, pk=tour_pk)
    participants = tour.participant_set.order_by('surname')

    context = {'tour': tour,
               'participants': participants}
    return render(request, 'guidedtours/view.html', context)


