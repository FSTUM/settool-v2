import os
import time

import unicodecsv as csv
from django import http
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.mail import EmailMessage
from django.db.models import Count, Q
from django.forms import modelformset_factory, forms
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.template import Template, Context
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from settool_common import utils
from settool_common.models import get_semester, Semester, Subject, Mail
from tutors.forms import TutorForm, TutorAdminForm, EventAdminForm, TaskAdminForm, RequirementAdminForm, AnswerForm, \
    TaskAssignmentForm, SettingsAdminForm, TutorMailAdminForm, SubjectTutorCountAssignmentAdminForm, \
    TutorAcceptAdminForm
from tutors.models import Tutor, Settings, Event, Task, Question, Answer, MailTutorTask, SubjectTutorCountAssignment
from tutors.tokens import account_activation_token


def tutor_signup(request):
    semester = get_object_or_404(Semester, pk=get_semester(request))
    settings = get_object_or_404(Settings, semester=semester)

    if not (settings.open_registration < timezone.now() < settings.close_registration):
        return render(request, 'tutors/tutor/registration_closed.html', {
            'start': settings.open_registration,
            'end': settings.close_registration
        })

    questions = Question.objects.filter(semester=semester)
    question_count = questions.count()
    answers_new = []
    for question in questions:
        a = Answer(question=question)
        answers_new.append(a)

    AnswerFormSet = modelformset_factory(Answer, form=AnswerForm,
                                         min_num=question_count,
                                         validate_min=True,
                                         max_num=question_count,
                                         validate_max=True,
                                         can_delete=False,
                                         can_order=False,
                                         extra=0)

    initial_data = [{'question': a.question.id, 'answer': a.answer} for a in answers_new]
    if request.method == 'POST':
        answer_formset = AnswerFormSet(request.POST, request.FILES, queryset=Answer.objects.none(),
                                       initial=initial_data)
    else:
        answer_formset = AnswerFormSet(queryset=Answer.objects.none(), initial=initial_data)

    form = TutorForm(request.POST or None, semester=semester)
    if form.is_valid() and answer_formset.is_valid():
        tutor = form.save()
        for answer in answer_formset:
            res = answer.save(commit=False)
            res.tutor_id = tutor.id
            res.save()
        tutor.log(None, "Signed up")

        context = Context({
            'tutor': tutor,
            'activation_url': request.build_absolute_uri(reverse('tutor_signup_confirm', kwargs={
                'uidb64': urlsafe_base64_encode(force_bytes(tutor.pk)).decode(),
                'token': account_activation_token.make_token(tutor)
            }))
        })
        message = Template(settings.mail_registration.text).render(context)
        subject = Template(settings.mail_registration.subject).render(context)
        to_email = form.cleaned_data.get('email')
        email = EmailMessage(
            from_email=settings.mail_registration.sender,
            to=[to_email],
            subject=subject,
            body=message
        )
        email.send()

        MailTutorTask.objects.create(tutor=tutor, mail=settings.mail_registration, task=None)

        return redirect('tutor_signup_confirmation_required')

    context = {'semester': semester,
               'answer_formset': answer_formset,
               'form': form}
    return render(request, 'tutors/tutor/signup.html', context)


def tutor_signup_success(request):
    return render(request, 'tutors/tutor/success.html')


def tutor_signup_invalid(request):
    return render(request, 'tutors/tutor/invalid.html')


def tutor_signup_confirmation_required(request):
    return render(request, 'tutors/tutor/confirmation_required.html')


def tutor_signup_confirm(request, uidb64, token):
    uid = urlsafe_base64_decode(uidb64).decode()
    tutor = get_object_or_404(Tutor, pk=uid)

    if account_activation_token.check_token(tutor, token):
        tutor.status = Tutor.STATUS_ACTIVE
        tutor.save()
        return redirect('tutor_signup_success')
    else:
        return redirect('tutor_signup_invalid')


@permission_required('tutors.edit_tutors')
def tutor_list(request, status=None):
    semester = get_object_or_404(Semester, pk=get_semester(request))

    if status is None:
        tutors = Tutor.objects.filter(semester=semester)
    else:
        tutors = Tutor.objects.filter(semester=semester, status=status)
    return render(request, 'tutors/tutor/list.html', {'tutors': tutors.order_by("registration_time"),
                                                      'status': status,
                                                      'questions': Question.objects.filter(semester=semester)})


def tutor_view(request, uid):
    tutor = get_object_or_404(Tutor, pk=uid)
    return render(request, 'tutors/tutor/view.html', {'tutor': tutor})


@permission_required('tutors.edit_tutors')
def tutor_change_status(request, uid, status):
    tutor = get_object_or_404(Tutor, pk=uid)
    form = forms.Form(request.POST or None)

    if form.is_valid() and status in [x for (x, y) in Tutor.STATUS_OPTIONS]:
        tutor.status = status
        tutor.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    return http.HttpResponseBadRequest()


@permission_required('tutors.edit_tutors')
def tutor_delete(request, uid):
    tutor = get_object_or_404(Tutor, pk=uid)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        tutor.delete()
        messages.success(request, 'Deleted Tutor %s.' % tutor)
        return redirect("tutor_list")

    context = {
        'tutor': tutor,
        'form': form
    }
    return render(request, 'tutors/tutor/delete.html', context)


def tutor_edit(request, uid):
    semester = get_object_or_404(Semester, pk=get_semester(request))
    tutor = get_object_or_404(Tutor, pk=uid)

    question_count = Question.objects.count()
    answers_existing = Answer.objects.filter(tutor=tutor)
    answers_new = []
    if len(answers_existing) != question_count:
        for question in Question.objects.filter(semester=semester):
            if answers_existing.filter(question=question).count() == 0:
                a = Answer(tutor=tutor, question=question)
                answers_new.append(a)

    AnswerFormSet = modelformset_factory(Answer, form=AnswerForm,
                                         min_num=question_count,
                                         validate_min=True,
                                         max_num=question_count,
                                         validate_max=True,
                                         can_delete=False,
                                         can_order=False)

    initial_data = [{'question': a.question.id, 'answer': a.answer} for a in answers_new]

    answer_formset = AnswerFormSet(request.POST or None, queryset=answers_existing, initial=initial_data)

    if request.user.has_perm('tutors.edit_tutors'):
        form = TutorAdminForm(request.POST or None, semester=tutor.semester, instance=tutor)
        if form.is_valid() and answer_formset.is_valid():
            form.save()
            for answer in answer_formset:
                res = answer.save(commit=False)
                res.tutor_id = tutor.id
                res.question_id = answer.cleaned_data.get('question').id
                res.save()
            tutor.log(request.user, "Tutor edited")
            messages.success(request, 'Saved Tutor %s.' % tutor)

            return redirect('tutor_view', tutor.id)

        return render(request, 'tutors/tutor/edit.html', {
            'form': form,
            'answer_formset': answer_formset,
            'tutor': tutor,
        })
    else:
        if answer_formset.is_valid():
            for answer in answer_formset:
                res = answer.save(commit=False)
                res.tutor_id = tutor.id
                res.save()
            tutor.log(request.user, "Tutor edited")
            messages.success(request, 'Saved Tutor %s.' % tutor)

            return redirect('tutor_view', tutor.id)

        return render(request, 'tutors/tutor/edit.html', {
            'answer_formset': answer_formset,
            'tutor': tutor,
        })


@permission_required('tutors.edit_tutors')
def event_edit(request, uid):
    event = get_object_or_404(Event, pk=uid)

    form = EventAdminForm(request.POST or None, semester=event.semester, instance=event)
    if form.is_valid():
        form.save()
        event.log(request.user, "Event edited")
        messages.success(request, 'Saved Event %s.' % event.name)

        return redirect('event_view', event.id)

    return render(request, 'tutors/event/edit.html', {
        'form': form,
        'event': event,
    })


@permission_required('tutors.edit_tutors')
def event_list(request):
    semester = get_object_or_404(Semester, pk=get_semester(request))
    events = Event.objects.filter(semester=semester).order_by('begin')
    return render(request, 'tutors/event/list.html', {'events': events})


@permission_required('tutors.edit_tutors')
def event_delete(request, uid):
    event = get_object_or_404(Event, pk=uid)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        event.delete()
        messages.success(request, 'Deleted Event %s.' % event.name)
        return redirect("event_list")

    context = {
        'event': event,
        'form': form
    }
    return render(request, 'tutors/event/delete.html', context)


@permission_required('tutors.edit_tutors')
def event_add(request):
    semester = get_object_or_404(Semester, pk=get_semester(request))

    form = EventAdminForm(request.POST or None, semester=semester)
    if form.is_valid():
        event = form.save()
        event.log(None, "Event added")
        messages.success(request, 'Added Event %s.' % event.name)

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
        messages.success(request, 'Saved Task %s.' % task.name)

        return redirect('task_view', task.id)

    return render(request, 'tutors/task/edit.html', {
        'form': form,
        'task': task,
    })


@permission_required('tutors.edit_tutors')
def task_list(request):
    semester = get_object_or_404(Semester, pk=get_semester(request))
    tasks = Task.objects.filter(semester=semester).order_by('begin')
    return render(request, 'tutors/task/list.html', {'tasks': tasks})


@permission_required('tutors.edit_tutors')
def task_delete(request, uid):
    task = get_object_or_404(Task, pk=uid)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        task.delete()
        messages.success(request, 'Deleted Task %s.' % task.name)
        return redirect("task_list")

    context = {
        'task': task,
        'form': form
    }
    return render(request, 'tutors/task/delete.html', context)


@permission_required('tutors.edit_tutors')
def task_add(request, eid=None):
    semester = get_object_or_404(Semester, pk=get_semester(request))

    form = TaskAdminForm(request.POST or None, semester=semester, initial={'event': eid})
    if form.is_valid():
        task = form.save()
        task.log(None, "Task added")
        messages.success(request, 'Added Task %s.' % task.name)

        return redirect('task_list')

    context = {'semester': semester,
               'form': form}
    return render(request, 'tutors/task/add.html', context)


def task_view(request, uid):
    semester = get_object_or_404(Semester, pk=get_semester(request))
    task = get_object_or_404(Task, pk=uid)

    if not request.user.has_perm('tutors.edit_tutors'):
        return render(request, 'tutors/task/view.html', {'task': task})

    form = TaskAssignmentForm(request.POST or None, semester=task.semester, instance=task)
    if form.is_valid():
        form.save()
        task.log(request.user, "Task Assignment edited")
        messages.success(request, 'Saved Task Assignment %s.' % task.name)

    assigned_tutors = task.tutors.all().order_by("last_name")
    parallel_task_tutors = Tutor.objects.filter(Q(task__begin__gte=task.begin) | Q(task__end__lte=task.end),
                                               Q(task__end__gt=task.begin),
                                               Q(task__begin__lt=task.end))
    context = {
        'task': task,
        'assigned_tutors': assigned_tutors,
        'unassigned_tutors': Tutor.objects.filter(semester=semester, status=Tutor.STATUS_ACCEPTED).exclude(
            id__in=assigned_tutors.values("id")).exclude(id__in=parallel_task_tutors.values("id")).order_by(
            "last_name"),
        'assignment_form': form,
    }
    return render(request, 'tutors/task/view.html', context)


@permission_required('tutors.edit_tutors')
def requirement_list(request):
    semester = get_object_or_404(Semester, pk=get_semester(request))
    questions = Question.objects.filter(semester=semester)
    return render(request, 'tutors/requirement/list.html', {'requirements': questions})


@permission_required('tutors.edit_tutors')
def requirement_view(request, uid):
    question = get_object_or_404(Question, pk=uid)
    return render(request, 'tutors/requirement/view.html', {'requirement': question})


@permission_required('tutors.edit_tutors')
def requirement_add(request):
    semester = get_object_or_404(Semester, pk=get_semester(request))

    form = RequirementAdminForm(request.POST or None, semester=semester)
    if form.is_valid():
        question = form.save()
        question.log(None, "Requirement added")
        messages.success(request, 'Added Requirement %s.' % question.question)

        return redirect('requirement_list')

    context = {'semester': semester,
               'form': form}
    return render(request, 'tutors/requirement/add.html', context)


@permission_required('tutors.edit_tutors')
def requirement_edit(request, uid):
    question = get_object_or_404(Question, pk=uid)

    form = RequirementAdminForm(request.POST or None, semester=question.semester, instance=question)
    if form.is_valid():
        form.save()
        question.log(request.user, "Question edited")
        messages.success(request, 'Saved Task %s.' % question.question)

        return redirect('requirement_view', question.id)

    return render(request, 'tutors/requirement/edit.html', {
        'form': form,
        'requirement': question,
    })


@permission_required('tutors.edit_tutors')
def requirement_delete(request, uid):
    question = get_object_or_404(Question, pk=uid)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        question.delete()
        messages.success(request, 'Deleted Question %s.' % question.question)
        return redirect("requirement_list")

    context = {
        'requirement': question,
        'form': form
    }
    return render(request, 'tutors/requirement/delete.html', context)


@permission_required('tutors.edit_tutors')
def task_mail(request, uid, template=None):
    semester = get_object_or_404(Semester, pk=get_semester(request))
    settings = get_object_or_404(Settings, semester=semester)
    task = get_object_or_404(Task, pk=uid)

    if template is None:
        template = settings.mail_task
        if template is None:
            raise Http404
    else:
        template = get_object_or_404(Mail, pk=template, sender=Mail.SET_TUTOR)

    tutor_data = {}
    for name, field in [(x.name, x) for x in Tutor._meta.fields if x.name not in ["semester", "subject"]]:
        if field.get_internal_type() == "CharField":
            tutor_data[name] = "<" + name + ">"
        else:
            tutor_data[name] = field.default

    tutor = Tutor(**tutor_data)

    context = Context({
        'task': task,
        'tutor': tutor,
    })

    subject = Template(template.subject).render(context)
    body = Template(template.text).render(context)

    form = TutorMailAdminForm(request.POST or None,
                              tutors=task.tutors.all(),
                              template=template,
                              semester=semester)
    if form.is_valid():
        tutors = form.cleaned_data["tutors"]
        mail_template = form.cleaned_data["mail_template"]

        for tutor in tutors:
            context = Context({
                'tutor': tutor,
                'task': task,
            })
            message = Template(mail_template.text).render(context)
            subject = Template(mail_template.subject).render(context)
            email = EmailMessage(
                from_email=mail_template.sender,
                to=[tutor.email],
                subject=subject,
                body=message
            )
            email.send()

            MailTutorTask.objects.create(tutor=tutor, mail=mail_template, task=task)

            task.log(request.user, "Send mail to %s." % tutor)

        messages.success(request, 'Send email for Task %s.' % task.name)
        return redirect("task_list")

    context = {
        "task": task,
        "from": template.sender,
        "subject": subject,
        "body": body,
        "form": form,
    }
    return render(request, 'tutors/task/mail.html', context)


@permission_required('tutors.edit_tutors')
def tutor_export(request, type, status=None):
    semester = get_object_or_404(Semester, pk=get_semester(request))

    if status is None:
        tutors = Tutor.objects.filter(semester=semester)
    else:
        tutors = Tutor.objects.filter(semester=semester, status=status)

    filename = "tutors_" + time.strftime("%Y%m%d-%H%M")

    if type == "pdf":
        return download_pdf("tutors/tex/tutors.tex", filename + ".pdf", {"tutors": tutors})
    elif type == "csv":
        return download_csv(["last_name", "first_name", "subject"], filename + ".csv", tutors)
    elif type == "tshirt":
        return download_pdf("tutors/tex/tshirts.tex", filename + ".pdf", {"tutors": tutors})

    raise Http404


@permission_required('tutors.edit_tutors')
def task_export(request, type, uid=None):
    task = Task.objects.get(pk=uid)

    filename = "task_" + task.id.__str__() + "_" + time.strftime("%Y%m%d-%H%M")
    if type == "pdf":
        return download_pdf("tutors/tex/task.tex", filename + ".pdf", {"task": task, "tutors": task.tutors.all()})

    raise Http404


def download_pdf(file, dest, context):
    pdf = utils.latex_to_pdf(file, context)
    response = HttpResponse(pdf, content_type="application/pdf")
    response['Content-Disposition'] = 'inline; filename=' + os.path.basename(dest)
    return response


def download_csv(fields, dest, context):
    response = HttpResponse(content_type="text/csv")
    response['Content-Disposition'] = 'inline; filename=' + os.path.basename(dest)
    writer = csv.writer(response, encoding='utf-8')
    writer.writerow(["nr"] + fields)

    for idx, obj in enumerate(context):
        row = [idx + 1]
        for field in fields:
            val = getattr(obj, field)
            if callable(val):
                val = val()
            else:
                val = val
            row.append(val)
        writer.writerow(row)
    return response


@permission_required('tutors.edit_tutors')
def tutors_settings_general(request):
    semester = get_object_or_404(Semester, pk=get_semester(request))
    all = Settings.objects.filter(semester=semester)
    if all.count() == 0:
        settings = None
    else:
        settings = all.first()

    form = SettingsAdminForm(request.POST or None, semester=semester, instance=settings)
    if form.is_valid():
        settings = form.save()
        settings.log(request.user, "Settings edited")
        messages.success(request, 'Saved Settings.')

        return redirect('tutors_settings_general')

    return render(request, 'tutors/settings/general.html', {
        'form': form,
    })


@permission_required('tutors.edit_tutors')
def tutors_settings_tutors(request):
    semester = get_object_or_404(Semester, pk=get_semester(request))

    subject_count = Subject.objects.all().count()
    subjects_existing = SubjectTutorCountAssignment.objects.filter(semester=semester)
    subjects_new = []
    if len(subjects_existing) != subject_count:
        for subject in Subject.objects.all():
            if subjects_existing.filter(subject=subject).count() == 0:
                a = SubjectTutorCountAssignment(subject=subject)
                subjects_new.append(a)

    CountFormSet = modelformset_factory(SubjectTutorCountAssignment, form=SubjectTutorCountAssignmentAdminForm,
                                        min_num=subject_count,
                                        validate_min=False,
                                        max_num=subject_count,
                                        validate_max=True,
                                        can_delete=False,
                                        can_order=False)

    initial_data = [{'subject': a.subject.id, 'wanted': a.wanted} for a in subjects_new]
    answer_formset = CountFormSet(request.POST or None,
                                  queryset=subjects_existing,
                                  initial=initial_data,
                                  form_kwargs={'semester': semester})
    if answer_formset.is_valid():
        for answer in answer_formset:
            res = answer.save(commit=False)
            res.semester = semester
            res.save()
            res.log(request.user, "Settings for tutor-subject counts edited")
        messages.success(request, 'Saved Settings.')

        return redirect('tutors_settings_tutors')

    return render(request, 'tutors/settings/tutors.html', {
        'form_set': answer_formset,
    })


@permission_required('tutors.edit_tutors')
def tutor_mail(request, status=None, template=None, uid=None):
    semester = get_object_or_404(Semester, pk=get_semester(request))
    settings = get_object_or_404(Settings, semester=semester)
    template = default_tutor_mail_template(semester, settings, status, template)

    if template is None:
        raise Http404

    if uid is None:
        if status is None:
            tutors = Tutor.objects.filter(semester=semester)
        else:
            tutors = Tutor.objects.filter(semester=semester, status=status)
    else:
        tutors = Tutor.objects.filter(pk=uid)

    tutor_data = {}
    for name, field in [(x.name, x) for x in Tutor._meta.fields if x.name not in ["semester", "subject"]]:
        if field.get_internal_type() == "CharField":
            tutor_data[name] = "<" + name + ">"
        else:
            tutor_data[name] = field.default

    if uid is None:
        tutor = Tutor(**tutor_data)
    else:
        tutor = tutors.first()

    context = Context({
        'tutor': tutor,
    })

    subject = Template(template.subject).render(context)
    body = Template(template.text).render(context)

    form = TutorMailAdminForm(request.POST or None,
                              tutors=tutors,
                              template=template,
                              semester=semester)
    if form.is_valid():
        tutors = form.cleaned_data["tutors"]
        mail_template = form.cleaned_data["mail_template"]

        for tutor in tutors:
            context = Context({
                'tutor': tutor,
            })
            message = Template(mail_template.text).render(context)
            subject = Template(mail_template.subject).render(context)
            email = EmailMessage(
                from_email=mail_template.sender,
                to=[tutor.email],
                subject=subject,
                body=message
            )
            email.send()

            MailTutorTask.objects.create(tutor=tutor, mail=mail_template, task=None)

            tutor.log(request.user, "Send mail to %s." % tutor)

        messages.success(request, 'Sent email to tutors.')
        return redirect("tutor_list") if status is None else redirect("tutor_list_status", status=status)

    context = {
        "from": template.sender,
        "subject": subject,
        "body": body,
        "form": form,
        "status": status,
        "template": template,
        "tutor": tutor,
    }
    return render(request, 'tutors/tutor/mail.html', context)


def default_tutor_mail_template(semester, settings, status, template):
    if template is None:
        status_to_template = {
            "active": settings.mail_waiting_list,
            "accepted": settings.mail_confirmed_place,
            "declined": settings.mail_declined_place,
        }

        if status in status_to_template:
            return status_to_template[status]

        return Mail.objects.filter(semester=semester, sender=Mail.SET_TUTOR).last()

    return get_object_or_404(Mail, pk=template, sender=Mail.SET_TUTOR)


@permission_required('tutors.edit_tutors')
def tutor_batch_accept(request):
    semester = get_object_or_404(Semester, pk=get_semester(request))
    tutors_active = Tutor.objects.filter(semester=semester, status=Tutor.STATUS_ACTIVE)
    tutors_accepted = Tutor.objects.filter(semester=semester, status=Tutor.STATUS_ACCEPTED)
    counts = SubjectTutorCountAssignment.objects.filter(semester=semester)

    tutor_ids = []
    to_be_accepted = {}

    for c in counts:
        active = tutors_active.filter(subject=c.subject)
        accepted_count = tutors_accepted.filter(subject=c.subject).count()

        if c.wanted > accepted_count:
            need = c.wanted - accepted_count
            for t in active.order_by("registration_time")[:need]:
                tutor_ids.append(t.id)

                if c.subject not in to_be_accepted:
                    to_be_accepted[c.subject] = []
                to_be_accepted[c.subject].append(t)

    form = TutorAcceptAdminForm(request.POST or None,
                                tutors=Tutor.objects.filter(id__in=tutor_ids),
                                semester=semester)
    if form.is_valid():
        tutors = form.cleaned_data["tutors"]
        for tutor in tutors:
            tutor.status = Tutor.STATUS_ACCEPTED
            tutor.save()

        return redirect("tutor_list_status", status=Tutor.STATUS_ACTIVE)

    context = {
        "to_be_accepted": to_be_accepted,
        "form": form
    }
    return render(request, 'tutors/tutor/batch_accept.html', context)


@permission_required('tutors.edit_tutors')
def tutor_batch_decline(request):
    semester = get_object_or_404(Semester, pk=get_semester(request))
    tutors_active = Tutor.objects.filter(semester=semester, status=Tutor.STATUS_ACTIVE)
    tutors_accepted = Tutor.objects.filter(semester=semester, status=Tutor.STATUS_ACCEPTED)
    counts = SubjectTutorCountAssignment.objects.filter(semester=semester)

    tutor_ids = []
    to_be_declined = {}

    for c in counts:
        active = tutors_active.filter(subject=c.subject)
        accepted_count = tutors_accepted.filter(subject=c.subject).count()

        keep = c.wanted - accepted_count + c.waitlist
        if keep < 0:
            keep = 0

        for t in active.order_by("registration_time")[keep:]:
            tutor_ids.append(t.id)

            if c.subject not in to_be_declined:
                to_be_declined[c.subject] = []
            to_be_declined[c.subject].append(t)

    form = TutorAcceptAdminForm(request.POST or None,
                                tutors=Tutor.objects.filter(id__in=tutor_ids),
                                semester=semester)
    if form.is_valid():
        tutors = form.cleaned_data["tutors"]
        for tutor in tutors:
            tutor.status = Tutor.STATUS_DECLINED
            tutor.save()

        return redirect("tutor_list_status", status=Tutor.STATUS_ACTIVE)

    context = {
        "to_be_declined": to_be_declined,
        "form": form
    }
    return render(request, 'tutors/tutor/batch_decline.html', context)


@permission_required('tutors.edit_tutors')
def dashboard(request):
    semester = get_object_or_404(Semester, pk=get_semester(request))

    counts = SubjectTutorCountAssignment.objects.filter(semester=semester)
    count_results = {}
    for c in counts:
        counts_tutors = Tutor.objects.filter(semester=semester, subject=c.subject, status=Tutor.STATUS_ACCEPTED). \
            aggregate(total=Count('subject'))
        if counts_tutors is None:
            count_results[c.subject] = (0, c.wanted)
        else:
            count_results[c.subject] = (counts_tutors['total'], c.wanted)

    events = Event.objects.filter(semester=semester).filter(
        Q(begin__gt=timezone.now()) | Q(end__gt=timezone.now())).order_by("begin")[:5]
    tasks = Task.objects.filter(semester=semester).filter(
        Q(begin__gt=timezone.now()) | Q(end__gt=timezone.now())).order_by("begin")[:5]

    missing_mails = 0
    for task in Task.objects.filter(semester=semester):
        missing_mails += Tutor.objects.filter(task=task).exclude(id__in=MailTutorTask.objects.filter(task=task).values(
            "tutor_id")).count()

    accepted_tutors = Tutor.objects.filter(semester=semester, status=Tutor.STATUS_ACCEPTED).count()
    waiting_tutors = Tutor.objects.filter(semester=semester, status=Tutor.STATUS_ACTIVE).count()
    return render(request, 'tutors/dashboard/dashboard.html', {
        'subject_counts': count_results,
        'events': events,
        'tasks': tasks,
        'missing_mails': missing_mails,
        'accepted_tutors': accepted_tutors,
        'waiting_tutors': waiting_tutors
    })
