from django.contrib.auth.decorators import permission_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from common.models import get_semester, Semester
from tutors.forms import TutorenForm, TutorenAdminForm, EventAdminForm, TaskAdminForm
from tutors.models import Tutor, Status, Registration, Event, Task
from tutors.tokens import account_activation_token


def tutor_signup(request):
    semester = get_object_or_404(Semester, pk=get_semester(request))
    registration = get_object_or_404(Registration, semester=semester)

    if not (registration.open_registration < timezone.now() < registration.close_registration):
        return render(request, 'tutors/tutor/registration_closed.html', {})

    form = TutorenForm(request.POST or None, semester=semester)
    if form.is_valid():
        tutor = form.save()
        tutor.log(None, "Signed up")

        mail_subject = 'Confirm your SET Tutor application.'
        message = render_to_string('tutors/tutor/signup_confirm.html', {
            'user': tutor,
            'domain': get_current_site(request).domain,
            'uid': urlsafe_base64_encode(force_bytes(tutor.pk)),
            'token': account_activation_token.make_token(tutor),
        })
        to_email = form.cleaned_data.get('email')
        email = EmailMessage(
            mail_subject, message, to=[to_email]
        )
        email.send()

        return redirect('tutor_signup_confirmation_required')

    context = {'semester': semester,
               'form': form}
    return render(request, 'tutors/tutor/signup.html', context)


def tutor_signup_success(request):
    return render(request, 'tutors/tutor/success.html')


def tutor_signup_invalid(request):
    return render(request, 'tutors/tutor/invalid.html')


def tutor_signup_confirmation_required(request):
    return render(request, 'tutors/tutor/confirmation_required.html')


def tutor_signup_confirm(request, uidb64, token):
    uid = force_text(urlsafe_base64_decode(uidb64))
    tutor = get_object_or_404(Tutor, pk=uid)

    if account_activation_token.check_token(tutor, token):
        tutor.status = Status.objects.get(key="active")
        tutor.save()
        return redirect('tutor_signup_success')
    else:
        return redirect('tutor_signup_invalid')


@permission_required('tutors.edit_tutors')
def tutor_list(request, status=None):
    if status is None:
        tutors = Tutor.objects.all()
    else:
        tutors = Tutor.objects.filter(status__key=status)
    return render(request, 'tutors/tutor/list.html', {'tutors': tutors})


def tutor_view(request, uid):
    tutor = get_object_or_404(Tutor, pk=uid)
    return render(request, 'tutors/tutor/view.html', {'tutor': tutor})


@permission_required('tutors.edit_tutors')
def tutor_accept(request, uid):
    tutor = get_object_or_404(Tutor, pk=uid)
    tutor.status = Status.objects.get(key='accepted')
    tutor.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


@permission_required('tutors.edit_tutors')
def tutor_decline(request, uid):
    tutor = get_object_or_404(Tutor, pk=uid)
    tutor.status = Status.objects.get(key='declined')
    tutor.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


@permission_required('tutors.edit_tutors')
def tutor_delete(request, uid):
    tutor = get_object_or_404(Tutor, pk=uid)
    tutor.delete()
    return redirect("tutor_list")


@permission_required('tutors.edit_tutors')
def tutor_edit(request, uid):
    tutor = get_object_or_404(Tutor, pk=uid)

    form = TutorenAdminForm(request.POST or None, semester=tutor.semester, instance=tutor)
    if form.is_valid():
        form.save()
        tutor.log(request.user, "Tutor edited")

        return redirect('tutor_view', tutor.id)

    return render(request, 'tutors/tutor/edit.html', {
        'form': form,
        'tutor': tutor,
    })


@permission_required('tutors.edit_tutors')
def event_edit(request, uid):
    event = get_object_or_404(Event, pk=uid)

    form = EventAdminForm(request.POST or None, semester=event.semester, instance=event)
    if form.is_valid():
        form.save()
        event.log(request.user, "Event edited")

        return redirect('event_view', event.id)

    return render(request, 'tutors/event/edit.html', {
        'form': form,
        'event': event,
    })


@permission_required('tutors.edit_tutors')
def event_list(request):
    events = Event.objects.all().order_by('begin')
    return render(request, 'tutors/event/list.html', {'events': events})


@permission_required('tutors.edit_tutors')
def event_delete(request, uid):
    event = get_object_or_404(Event, pk=uid)
    event.delete()
    return redirect("event_list")


@permission_required('tutors.edit_tutors')
def event_add(request):
    semester = get_object_or_404(Semester, pk=get_semester(request))

    form = EventAdminForm(request.POST or None, semester=semester)
    if form.is_valid():
        event = form.save()
        event.log(None, "Event added")

        return redirect('event_list')

    context = {'semester': semester,
               'form': form}
    return render(request, 'tutors/event/add.html', context)


def event_view(request, uid):
    event = get_object_or_404(Event, pk=uid)
    return render(request, 'tutors/event/view.html', {'event': event})


@permission_required('tutors.edit_tutors')
def task_edit(request, uid):
    task = get_object_or_404(Task, pk=uid)

    form = TaskAdminForm(request.POST or None, semester=task.semester, instance=task)
    if form.is_valid():
        form.save()
        task.log(request.user, "Task edited")

        return redirect('task_view', task.id)

    return render(request, 'tutors/task/edit.html', {
        'form': form,
        'task': task,
    })


@permission_required('tutors.edit_tutors')
def task_list(request):
    tasks = Task.objects.all().order_by('begin')
    return render(request, 'tutors/task/list.html', {'tasks': tasks})


@permission_required('tutors.edit_tutors')
def task_delete(request, uid):
    task = get_object_or_404(Task, pk=uid)
    task.delete()
    return redirect("task_list")


@permission_required('tutors.edit_tutors')
def task_add(request):
    semester = get_object_or_404(Semester, pk=get_semester(request))

    form = TaskAdminForm(request.POST or None, semester=semester)
    if form.is_valid():
        task = form.save()
        task.log(None, "Task added")

        return redirect('task_list')

    context = {'semester': semester,
               'form': form}
    return render(request, 'tutors/task/add.html', context)


def task_view(request, uid):
    task = get_object_or_404(Task, pk=uid)
    return render(request, 'tutors/task/view.html', {'task': task})
