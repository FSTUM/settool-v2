import time
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from django import http
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Count, Manager, Q, QuerySet
from django.forms import forms, modelformset_factory
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.template import Context, Template
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _
from django_tex.response import PDFResponse
from django_tex.shortcuts import render_to_pdf

from settool_common import utils
from settool_common.models import get_semester, Semester, Subject
from tutors.forms import (
    AnswerForm,
    CollaboratorForm,
    EventAdminForm,
    RequirementAdminForm,
    SettingsAdminForm,
    SubjectTutorCountAssignmentAdminForm,
    TaskAdminForm,
    TaskAssignmentForm,
    TutorAcceptAdminForm,
    TutorAdminForm,
    TutorForm,
    TutorMailAdminForm,
)
from tutors.models import (
    Answer,
    Event,
    MailTutorTask,
    Question,
    Settings,
    SubjectTutorCountAssignment,
    Task,
    Tutor,
    TutorMail,
)
from tutors.tokens import account_activation_token


def tutor_signup(request: WSGIRequest) -> HttpResponse:
    semester = get_object_or_404(Semester, pk=get_semester(request))
    settings = get_object_or_404(Settings, semester=semester)

    if not settings.registration_open():
        return render(
            request,
            "tutors/standalone/tutor_signup/registration_closed.html",
            {
                "start": settings.open_registration,
                "end": settings.close_registration,
            },
        )

    answer_formset = generate_answer_formset(request, semester)
    form = TutorForm(request.POST or None, semester=semester)
    if form.is_valid() and answer_formset.is_valid():
        if settings.mail_registration is None:
            messages.error(
                request,
                _(
                    "We did not configure a mail to send to you in case you registered. Please Contact {mail} and "
                    "tell us about this error. We are verry sorry about this inconvinience. To make up for it cute "
                    "cat-images: https://imgur.com/gallery/3OMii",
                ).format(mail=TutorMail.SET_TUTOR),
            )
            return redirect("tutor_signup")
        tutor = form.save()
        tutor.log(None, "Signed up")
        save_answer_formset(answer_formset, tutor.id)

        activation_url = request.build_absolute_uri(
            reverse(
                "tutor_signup_confirm",
                kwargs={
                    "uidb64": urlsafe_base64_encode(force_bytes(tutor.pk)),
                    "token": account_activation_token.make_token(tutor),
                },
            ),
        )
        if not settings.mail_registration.send_mail_registration(tutor, activation_url):
            messages.error(
                request,
                _("Could not send email. If this error persists send a mail to {mail}").format(mail=TutorMail.SET),
            )
            return redirect("tutor_signup")
        MailTutorTask.objects.create(tutor=tutor, mail=settings.mail_registration, task=None)
        return redirect("tutor_signup_confirmation_required")

    context = {
        "semester": semester,
        "answer_formset": answer_formset,
        "form": form,
    }
    return render(request, "tutors/standalone/tutor_signup/signup.html", context)


def save_answer_formset(answer_formset, tutor_id):
    answer: AnswerForm
    for answer in answer_formset:
        res = answer.save(commit=False)
        res.tutor_id = tutor_id
        res.save()


def collaborator_signup(request: WSGIRequest) -> HttpResponse:
    semester = get_object_or_404(Semester, pk=get_semester(request))
    settings = get_object_or_404(Settings, semester=semester)

    if not settings.registration_open():
        return render(
            request,
            "tutors/standalone/collaborator_signup/registration_closed.html",
            {
                "start": settings.open_registration,
                "end": settings.close_registration,
            },
        )

    answer_formset = generate_answer_formset(request, semester)
    form = CollaboratorForm(request.POST or None, semester=semester)
    if form.is_valid() and answer_formset.is_valid():
        collaborator: Tutor = form.save(commit=False)
        collaborator.status = Tutor.STATUS_EMPLOYEE
        collaborator.save()
        collaborator.log(None, "Signed up")
        save_answer_formset(answer_formset, collaborator.id)
        return redirect("collaborator_signup_success")

    context = {
        "semester": semester,
        "answer_formset": answer_formset,
        "form": form,
    }
    return render(request, "tutors/standalone/collaborator_signup/signup.html", context)


def generate_answer_formset(request: WSGIRequest, semester: Semester) -> Any:
    questions = Question.objects.filter(semester=semester)
    question_count = questions.count()
    answers_new = []
    for question in questions:
        answers_new.append(Answer(question=question))
    # pylint: disable=invalid-name
    AnswerFormSet = modelformset_factory(
        Answer,
        form=AnswerForm,
        min_num=question_count,
        validate_min=True,
        max_num=question_count,
        validate_max=True,
        can_delete=False,
        can_order=False,
        extra=0,
    )
    initial_data = [{"question": a.question.id, "answer": a.answer} for a in answers_new]
    if request.method == "POST":
        return AnswerFormSet(
            request.POST,
            request.FILES,
            queryset=Answer.objects.none(),
            initial=initial_data,
        )
    return AnswerFormSet(queryset=Answer.objects.none(), initial=initial_data)


def collaborator_signup_success(request: WSGIRequest) -> HttpResponse:
    return render(request, "tutors/standalone/collaborator_signup/success.html")


def tutor_signup_success(request: WSGIRequest) -> HttpResponse:
    return render(request, "tutors/standalone/tutor_signup/success.html")


def tutor_signup_invalid(request: WSGIRequest) -> HttpResponse:
    return render(request, "tutors/standalone/tutor_signup/invalid.html")


def tutor_signup_confirmation_required(request: WSGIRequest) -> HttpResponse:
    return render(request, "tutors/standalone/tutor_signup/confirmation_required.html")


def tutor_signup_confirm(request: WSGIRequest, uidb64: Any, token: Any) -> HttpResponse:
    uid = urlsafe_base64_decode(uidb64).decode()
    tutor = get_object_or_404(Tutor, pk=uid)

    if account_activation_token.check_token(tutor, token):  # type: ignore
        # TODO Check if tutor can be made subclass of User.. current Version works, but is inelegant
        tutor.status = Tutor.STATUS_ACTIVE
        tutor.save()
        return redirect("tutor_signup_success")
    return redirect("tutor_signup_invalid")


@permission_required("tutors.edit_tutors")
def tutor_list(request: WSGIRequest, status: str) -> HttpResponse:
    semester = get_object_or_404(Semester, pk=get_semester(request))

    if status == "all":
        tutors = Tutor.objects.filter(semester=semester)
    else:
        tutors = Tutor.objects.filter(semester=semester, status=status)
    return render(
        request,
        "tutors/tutor/list.html",
        {
            "tutors": tutors.order_by("registration_time"),
            "status": status,
            "questions": Question.objects.filter(semester=semester),
        },
    )


def tutor_view(request: WSGIRequest, uid: UUID) -> HttpResponse:
    tutor = get_object_or_404(Tutor, pk=uid)
    return render(request, "tutors/tutor/view.html", {"tutor": tutor})


@permission_required("tutors.edit_tutors")
def tutor_change_status(request: WSGIRequest, uid: UUID, status: str) -> HttpResponse:
    tutor = get_object_or_404(Tutor, pk=uid)
    form = forms.Form(request.POST or None)

    if form.is_valid() and status in (x for x, _ in Tutor.STATUS_OPTIONS):
        tutor.status = status
        tutor.save()
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
    return http.HttpResponseBadRequest()


@permission_required("tutors.edit_tutors")
def tutor_delete(request: WSGIRequest, uid: UUID) -> HttpResponse:
    tutor = get_object_or_404(Tutor, pk=uid)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        tutor.delete()
        messages.success(request, f"Deleted Tutor {tutor}.")
        return redirect("tutor_list_status_all")

    context = {
        "tutor": tutor,
        "form": form,
    }
    return render(request, "tutors/tutor/delete.html", context)


@permission_required("tutors.edit_tutors")
def tutor_edit(request: WSGIRequest, uid: UUID) -> HttpResponse:
    semester = get_object_or_404(Semester, pk=get_semester(request))
    tutor = get_object_or_404(Tutor, pk=uid)

    question_count = Question.objects.filter(semester=semester).count()
    answers_existing = Answer.objects.filter(tutor=tutor)
    answers_new = []
    if len(answers_existing) != question_count:
        for question in Question.objects.filter(semester=semester):
            if answers_existing.filter(question=question).count() == 0:
                answers_new.append(Answer(tutor=tutor, question=question))

    # pylint: disable=invalid-name
    AnswerFormSet = modelformset_factory(
        Answer,
        form=AnswerForm,
        min_num=question_count,
        validate_min=True,
        max_num=question_count,
        validate_max=True,
        can_delete=False,
        can_order=False,
    )

    initial_data = [{"question": a.question.id, "answer": a.answer} for a in answers_new]

    answer_formset = AnswerFormSet(
        request.POST or None,
        queryset=answers_existing,
        initial=initial_data,
    )

    form = TutorAdminForm(request.POST or None, semester=tutor.semester, instance=tutor)
    if form.is_valid() and answer_formset.is_valid():
        form.save()
        answer: AnswerForm
        for answer in answer_formset:
            res = answer.save(commit=False)
            res.tutor_id = tutor.id
            res.question_id = answer.cleaned_data.get("question").id
            res.save()
        tutor.log(request.user, "Tutor edited")
        messages.success(request, f"Saved Tutor {tutor}.")

        return redirect("tutor_view", tutor.id)

    return render(
        request,
        "tutors/tutor/edit.html",
        {
            "form": form,
            "answer_formset": answer_formset,
            "tutor": tutor,
        },
    )


@permission_required("tutors.edit_tutors")
def event_edit(request: WSGIRequest, uid: UUID) -> HttpResponse:
    event = get_object_or_404(Event, pk=uid)

    form = EventAdminForm(request.POST or None, semester=event.semester, instance=event)
    if form.is_valid():
        form.save()
        event.log(request.user, "Event edited")
        messages.success(request, f"Saved Event {event.name}.")

        return redirect("event_view", event.id)

    return render(
        request,
        "tutors/event/edit.html",
        {
            "form": form,
            "event": event,
        },
    )


@permission_required("tutors.edit_tutors")
def event_list(request: WSGIRequest) -> HttpResponse:
    semester = get_object_or_404(Semester, pk=get_semester(request))
    events = Event.objects.filter(semester=semester).order_by("begin")
    return render(request, "tutors/event/list.html", {"events": events})


@permission_required("tutors.edit_tutors")
def event_delete(request: WSGIRequest, uid: UUID) -> HttpResponse:
    event = get_object_or_404(Event, pk=uid)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        event.delete()
        messages.success(request, f"Deleted Event {event.name}.")
        return redirect("event_list")

    context = {
        "event": event,
        "form": form,
    }
    return render(request, "tutors/event/delete.html", context)


@permission_required("tutors.edit_tutors")
def event_add(request: WSGIRequest) -> HttpResponse:
    semester = get_object_or_404(Semester, pk=get_semester(request))

    form = EventAdminForm(request.POST or None, semester=semester)
    if form.is_valid():
        event = form.save()
        event.log(None, "Event added")
        messages.success(request, f"Added Event {event.name}.")

        return redirect("event_list")

    context = {
        "semester": semester,
        "form": form,
    }
    return render(request, "tutors/event/add.html", context)


def event_view(request: WSGIRequest, uid: UUID) -> HttpResponse:
    event = get_object_or_404(Event, pk=uid)
    return render(request, "tutors/event/view.html", {"event": event})


@permission_required("tutors.edit_tutors")
def task_edit(request: WSGIRequest, uid: UUID) -> HttpResponse:
    task = get_object_or_404(Task, pk=uid)

    form = TaskAdminForm(request.POST or None, semester=task.semester, instance=task)
    if form.is_valid():
        form.save()
        task.log(request.user, "Task edited")
        messages.success(request, f"Saved Task {task.name}.")

        return redirect("task_view", task.id)

    return render(
        request,
        "tutors/task/edit.html",
        {
            "form": form,
            "task": task,
        },
    )


@permission_required("tutors.edit_tutors")
def task_list(request: WSGIRequest) -> HttpResponse:
    tasks = Task.objects.filter(semester=get_semester(request)).order_by("begin")
    return render(request, "tutors/task/list.html", {"tasks": tasks})


@permission_required("tutors.edit_tutors")
def task_delete(request: WSGIRequest, uid: UUID) -> HttpResponse:
    task = get_object_or_404(Task, pk=uid)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        task.delete()
        messages.success(request, f"Deleted Task {task.name}.")
        return redirect("task_list")

    context = {
        "task": task,
        "form": form,
    }
    return render(request, "tutors/task/delete.html", context)


@permission_required("tutors.edit_tutors")
def task_add(request: WSGIRequest, eid: Optional[UUID] = None) -> HttpResponse:
    semester = get_object_or_404(Semester, pk=get_semester(request))

    form = TaskAdminForm(request.POST or None, semester=semester, initial={"event": eid})
    if form.is_valid():
        task = form.save()
        task.log(None, "Task added")
        messages.success(request, f"Added Task {task.name}.")

        return redirect("task_list")

    context = {
        "semester": semester,
        "form": form,
    }
    return render(request, "tutors/task/add.html", context)


def task_view(request: WSGIRequest, uid: UUID) -> HttpResponse:
    semester = get_object_or_404(Semester, pk=get_semester(request))
    task = get_object_or_404(Task, pk=uid)

    if not request.user.has_perm("tutors.edit_tutors"):
        return render(request, "tutors/task/view.html", {"task": task})

    form = TaskAssignmentForm(request.POST or None, semester=task.semester, instance=task)
    if form.is_valid():
        form.save()
        task.log(request.user, "Task Assignment edited")
        messages.success(request, f"Saved Task Assignment {task.name}.")

    assigned_tutors = task.tutors.all().order_by("last_name")
    parallel_task_tutors = Tutor.objects.filter(
        Q(task__begin__gte=task.begin) | Q(task__end__lte=task.end),
        Q(task__end__gt=task.begin),
        Q(task__begin__lt=task.end),
    )
    unassigned_tutors = (
        Tutor.objects.filter(semester=semester, status=Tutor.STATUS_ACCEPTED)
        .exclude(id__in=assigned_tutors.values("id"))
        .exclude(id__in=parallel_task_tutors.values("id"))
        .order_by("last_name")
    )
    context = {
        "task": task,
        "assigned_tutors": assigned_tutors,
        "unassigned_tutors": unassigned_tutors,
        "assignment_form": form,
    }
    return render(request, "tutors/task/view.html", context)


@permission_required("tutors.edit_tutors")
def requirement_list(request: WSGIRequest) -> HttpResponse:
    semester = get_object_or_404(Semester, pk=get_semester(request))
    questions = Question.objects.filter(semester=semester)
    return render(request, "tutors/requirement/list.html", {"requirements": questions})


@permission_required("tutors.edit_tutors")
def requirement_view(request: WSGIRequest, uid: UUID) -> HttpResponse:
    question = get_object_or_404(Question, pk=uid)
    return render(request, "tutors/requirement/view.html", {"requirement": question})


@permission_required("tutors.edit_tutors")
def requirement_add(request: WSGIRequest) -> HttpResponse:
    semester = get_object_or_404(Semester, pk=get_semester(request))

    form = RequirementAdminForm(request.POST or None, semester=semester)
    if form.is_valid():
        question = form.save()
        question.log(None, "Requirement added")
        messages.success(request, f"Added Requirement {question.question}.")

        return redirect("requirement_list")

    context = {
        "semester": semester,
        "form": form,
    }
    return render(request, "tutors/requirement/add.html", context)


@permission_required("tutors.edit_tutors")
def requirement_edit(request: WSGIRequest, uid: UUID) -> HttpResponse:
    question = get_object_or_404(Question, pk=uid)

    form = RequirementAdminForm(request.POST or None, semester=question.semester, instance=question)
    if form.is_valid():
        form.save()
        question.log(request.user, "Question edited")
        messages.success(request, f"Saved Task {question.question}.")

        return redirect("requirement_view", question.id)

    return render(
        request,
        "tutors/requirement/edit.html",
        {
            "form": form,
            "requirement": question,
        },
    )


@permission_required("tutors.edit_tutors")
def requirement_delete(request: WSGIRequest, uid: UUID) -> HttpResponse:
    question = get_object_or_404(Question, pk=uid)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        question.delete()
        messages.success(request, f"Deleted Question {question.question}.")
        return redirect("requirement_list")

    context = {
        "requirement": question,
        "form": form,
    }
    return render(request, "tutors/requirement/delete.html", context)


@permission_required("tutors.edit_tutors")
def task_mail(request: WSGIRequest, uid: UUID, mail_pk: Optional[int] = None) -> HttpResponse:
    semester = get_object_or_404(Semester, pk=get_semester(request))
    settings = get_object_or_404(Settings, semester=semester)
    task = get_object_or_404(Task, pk=uid)

    if mail_pk is None:
        mail = settings.mail_task
        if mail is None:
            raise Http404
    else:
        mail = get_object_or_404(TutorMail, pk=mail_pk)

    tutor_data = extract_tutor_data()
    tutor = Tutor(**tutor_data)
    form = TutorMailAdminForm(
        request.POST or None,
        tutors=task.tutors.all(),
        template=mail,
        semester=semester,
    )
    if form.is_valid():
        tutors = form.cleaned_data["tutors"]
        mail_template: TutorMail = form.cleaned_data["mail_template"]

        for tutor in tutors:
            if mail_template.send_mail_task(tutor, task):
                MailTutorTask.objects.create(tutor=tutor, mail=mail_template, task=task)
                task.log(request.user, f"Send mail to {tutor}.")
            else:
                messages.error(
                    request,
                    _("Could not send email to {first_name} {last_name} ({email}).").format(
                        first_name=tutor.first_name,
                        last_name=tutor.last_name,
                        email=tutor.email,
                    ),
                )

        messages.success(request, f"Send email for {task.name}.")
        return redirect("task_list")
    subject, text, sender = mail.get_mail_task(tutor, task)
    context = {
        "task": task,
        "from": sender,
        "subject": subject,
        "body": text,
        "form": form,
    }
    return render(request, "tutors/task/mail.html", context)


@permission_required("tutors.edit_tutors")
def tutor_export(request: WSGIRequest, file_type: str, status: str = "all") -> Union[HttpResponse, PDFResponse]:
    semester = get_object_or_404(Semester, pk=get_semester(request))

    if status == "all":
        tutors = Tutor.objects.filter(semester=semester)
    else:
        tutors = Tutor.objects.filter(semester=semester, status=status)
    tutors = tutors.order_by("last_name", "first_name")

    filename = f"tutors_{time.strftime('%Y%m%d-%H%M')}"

    if file_type == "pdf":
        return render_to_pdf(request, "tutors/tex/tutors.tex", {"tutors": tutors}, f"{filename}.pdf")
    if file_type == "csv":
        return utils.download_csv(
            ["last_name", "first_name", "subject", "matriculation_number", "birthday"],
            f"{filename}.csv",
            list(tutors),
        )
    if file_type == "tshirt":
        return render_to_pdf(request, "tutors/tex/tshirts.tex", {"tutors": tutors}, f"{filename}.pdf")

    raise Http404


@permission_required("tutors.edit_tutors")
def task_export(request: WSGIRequest, file_type: str, uid: UUID) -> PDFResponse:
    task = get_object_or_404(Task, pk=uid)
    tutors = task.tutors.order_by("last_name", "first_name")

    filename = f"task_{task.id}_{time.strftime('%Y%m%d-%H%M')}"
    if file_type == "pdf":
        return render_to_pdf(request, "tutors/tex/task.tex", {"task": task, "tutors": tutors}, f"{filename}.pdf")
    raise Http404


@permission_required("tutors.edit_tutors")
def tutors_settings_general(request: WSGIRequest) -> HttpResponse:
    semester = get_object_or_404(Semester, pk=get_semester(request))
    all_tutor_settings = Settings.objects.filter(semester=semester)
    if all_tutor_settings.count() == 0:
        settings = None
    else:
        settings = all_tutor_settings.first()

    form = SettingsAdminForm(request.POST or None, semester=semester, instance=settings)
    if form.is_valid():
        settings = form.save()
        if settings:
            settings.log(request.user, "Settings edited")
            messages.success(request, "Saved Settings.")
        else:
            messages.error(request, "The Settings do not exist.")

        return redirect("tutors_settings_general")

    return render(
        request,
        "tutors/settings/general.html",
        {
            "form": form,
        },
    )


@permission_required("tutors.edit_tutors")
def tutors_settings_tutors(request: WSGIRequest) -> HttpResponse:
    semester = get_object_or_404(Semester, pk=get_semester(request))

    subject_count = Subject.objects.all().count()
    subjects_existing = SubjectTutorCountAssignment.objects.filter(semester=semester)
    subjects_new = []
    if len(subjects_existing) != subject_count:
        for subject in Subject.objects.all():
            if subjects_existing.filter(subject=subject).count() == 0:
                subjects_new.append(SubjectTutorCountAssignment(subject=subject))

    # pylint: disable=invalid-name
    CountFormSet = modelformset_factory(
        SubjectTutorCountAssignment,
        form=SubjectTutorCountAssignmentAdminForm,
        min_num=subject_count,
        validate_min=False,
        max_num=subject_count,
        validate_max=True,
        can_delete=False,
        can_order=False,
    )

    initial_data = [
        {
            "subject": tutor_subject_assignment.subject.id,
            "wanted": tutor_subject_assignment.wanted,
        }
        for tutor_subject_assignment in subjects_new
    ]
    answer_formset = CountFormSet(
        request.POST or None,
        queryset=subjects_existing,
        initial=initial_data,
        form_kwargs={"semester": semester},
    )
    if answer_formset.is_valid():
        answer: AnswerForm
        for answer in answer_formset:
            res = answer.save(commit=False)
            res.semester = semester
            res.save()
            res.log(request.user, "Settings for tutor-subject counts edited")
        messages.success(request, "Saved Settings.")

        return redirect("tutors_settings_tutors")

    return render(
        request,
        "tutors/settings/tutors.html",
        {
            "form_set": answer_formset,
        },
    )


@permission_required("tutors.edit_tutors")
def tutor_mail(
    request: WSGIRequest,
    status: str = "all",
    mail_pk: Optional[int] = None,
    uid: Optional[UUID] = None,
) -> HttpResponse:
    semester = get_object_or_404(Semester, pk=get_semester(request))
    settings = get_object_or_404(Settings, semester=semester)
    template = default_tutor_mail(settings, status, mail_pk)

    if template is None:
        raise Http404

    if uid is None:
        if status == "all":
            tutors: Manager[Tutor] = Tutor.objects.filter(semester=semester)
        else:
            tutors = Tutor.objects.filter(semester=semester, status=status)
        tutor_data = extract_tutor_data()
        tutor: Tutor = Tutor(**tutor_data)
    else:
        tutors = Tutor.objects.filter(pk=uid)
        tutor = get_object_or_404(Tutor, pk=uid)

    mail_context = Context(
        {
            "tutor": tutor,
        },
    )

    subject = Template(template.subject).render(mail_context)
    body = Template(template.text).render(mail_context)

    form = TutorMailAdminForm(
        request.POST or None,
        tutors=tutors,
        template=template,
        semester=semester,
    )
    if form.is_valid():
        tutors = form.cleaned_data["tutors"]
        mail_template = form.cleaned_data["mail_template"]

        send_email_to_all_tutors(mail_template, list(tutors), request)

        return redirect(f"tutor_list_status_{status}")

    context: Dict[str, Any] = {
        "from": template.sender,
        "subject": subject,
        "body": body,
        "form": form,
        "status": status,
        "template": template,
        "tutor": tutor,
    }
    return render(request, "tutors/tutor/mail.html", context)


def extract_tutor_data() -> Dict[str, str]:
    tutor_data = {}
    for field in Tutor._meta.fields:
        if field.name not in ["semester", "subject"]:
            if field.get_internal_type() == "CharField":
                tutor_data[field.name] = f"<{field.name}>"
            else:
                tutor_data[field.name] = field.default
    return tutor_data


def send_email_to_all_tutors(
    mail_template: TutorMail,
    tutors: List[Tutor],
    request: WSGIRequest,
) -> None:
    for tutor in tutors:
        if mail_template.send_mail_tutor(tutor):
            MailTutorTask.objects.create(tutor=tutor, mail=mail_template, task=None)
            tutor.log(request.user, f"Send mail to {tutor}.")
        else:
            tutor.log(request.user, f"Failed to send mail to {tutor}.")
            messages.error(
                request,
                _("Could not send email to {first_name} {last_name} ({email}).").format(
                    first_name=tutor.first_name,
                    last_name=tutor.last_name,
                    email=tutor.email,
                ),
            )
    messages.success(request, "Sent email to tutors.")


def default_tutor_mail(
    settings: Settings,
    status: str,
    mail_pk: Optional[int],
) -> Optional[TutorMail]:
    if mail_pk is None:
        status_to_template = {
            "active": settings.mail_waiting_list,
            "accepted": settings.mail_confirmed_place,
            "declined": settings.mail_declined_place,
        }

        if status in status_to_template:
            return status_to_template[status]

        return TutorMail.objects.filter(sender=TutorMail.SET_TUTOR).last()

    return get_object_or_404(TutorMail, pk=mail_pk, sender=TutorMail.SET_TUTOR)


@permission_required("tutors.edit_tutors")
def tutor_batch_accept(request: WSGIRequest) -> HttpResponse:
    semester = get_object_or_404(Semester, pk=get_semester(request))
    tutors_active = Tutor.objects.filter(semester=semester, status=Tutor.STATUS_ACTIVE)
    tutors_accepted = Tutor.objects.filter(semester=semester, status=Tutor.STATUS_ACCEPTED)
    assignments_wish_counter = SubjectTutorCountAssignment.objects.filter(semester=semester)

    tutor_ids: List[UUID] = []
    to_be_accepted: Dict[Subject, List[Tutor]] = {}

    for assignment_wish_counter in assignments_wish_counter:
        if not (
            assignment_wish_counter.subject and assignment_wish_counter.wanted and assignment_wish_counter.waitlist
        ):
            return redirect("tutors_settings_general")
        active_tutors = tutors_active.filter(subject=assignment_wish_counter.subject)
        accepted_count: int = tutors_accepted.filter(
            subject=assignment_wish_counter.subject,
        ).count()

        if assignment_wish_counter.wanted > accepted_count:
            need: int = assignment_wish_counter.wanted - accepted_count
            tutor: Tutor
            for tutor in active_tutors.order_by("registration_time")[:need]:
                tutor_ids.append(tutor.id)

                if assignment_wish_counter.subject not in to_be_accepted:
                    to_be_accepted[assignment_wish_counter.subject] = []
                to_be_accepted[assignment_wish_counter.subject].append(tutor)

    form = TutorAcceptAdminForm(
        request.POST or None,
        tutors=Tutor.objects.filter(id__in=tutor_ids),
        semester=semester,
    )
    if form.is_valid():
        tutors: List[Tutor] = form.cleaned_data["tutors"]
        accepted_tutor: Tutor
        for accepted_tutor in tutors:
            accepted_tutor.status = Tutor.STATUS_ACCEPTED
            accepted_tutor.save()

        return redirect("tutor_list_status_active")

    context = {
        "to_be_accepted": to_be_accepted,
        "form": form,
    }
    return render(request, "tutors/tutor/batch_accept.html", context)


@permission_required("tutors.edit_tutors")
def tutor_batch_decline(request: WSGIRequest) -> HttpResponse:
    semester = get_object_or_404(Semester, pk=get_semester(request))
    tutors_active = Tutor.objects.filter(semester=semester, status=Tutor.STATUS_ACTIVE)
    tutors_accepted = Tutor.objects.filter(semester=semester, status=Tutor.STATUS_ACCEPTED)
    assignments_wish_counter = SubjectTutorCountAssignment.objects.filter(semester=semester)

    tutor_ids: List[UUID] = []
    to_be_declined: Dict[Subject, List[Tutor]] = {}

    for assignment_wish_counter in assignments_wish_counter:
        if not (
            assignment_wish_counter.subject and assignment_wish_counter.wanted and assignment_wish_counter.waitlist
        ):
            return redirect("tutors_settings_general")
        active_tutors = tutors_active.filter(subject=assignment_wish_counter.subject)
        accepted_count: int = tutors_accepted.filter(
            subject=assignment_wish_counter.subject,
        ).count()

        keep: int = assignment_wish_counter.wanted - accepted_count + assignment_wish_counter.waitlist
        if keep < 0:
            keep = 0

        for tutor in active_tutors.order_by("registration_time")[keep:]:
            tutor_ids.append(tutor.id)

            if assignment_wish_counter.subject not in to_be_declined:
                to_be_declined[assignment_wish_counter.subject] = []
            to_be_declined[assignment_wish_counter.subject].append(tutor)

    form = TutorAcceptAdminForm(
        request.POST or None,
        tutors=Tutor.objects.filter(id__in=tutor_ids),
        semester=semester,
    )
    if form.is_valid():
        tutors = form.cleaned_data["tutors"]
        for tutor in tutors:
            tutor.status = Tutor.STATUS_DECLINED
            tutor.save()

        return redirect("tutor_list_status_active")

    context = {
        "to_be_declined": to_be_declined,
        "form": form,
    }
    return render(request, "tutors/tutor/batch_decline.html", context)


@permission_required("tutors.edit_tutors")
def dashboard(request: WSGIRequest) -> HttpResponse:
    semester = get_object_or_404(Semester, pk=get_semester(request))

    assignments_wish_counter: QuerySet[SubjectTutorCountAssignment]
    assignments_wish_counter = SubjectTutorCountAssignment.objects.filter(semester=semester)
    count_results = {}
    for assignment_wish_counter in assignments_wish_counter:
        counts_tutors: Dict[str, int] = Tutor.objects.filter(
            semester=semester,
            subject=assignment_wish_counter.subject,
            status=Tutor.STATUS_ACCEPTED,
        ).aggregate(total=Count("subject"))
        count_results[assignment_wish_counter.subject] = (
            counts_tutors["total"] or 0,
            assignment_wish_counter.wanted,
        )

    events = (
        Event.objects.filter(semester=semester)
        .filter(Q(begin__gt=timezone.now()) | Q(end__gt=timezone.now()))
        .order_by("begin")[:5]
    )
    tasks = (
        Task.objects.filter(semester=semester)
        .filter(Q(begin__gt=timezone.now()) | Q(end__gt=timezone.now()))
        .order_by("begin")[:5]
    )

    missing_mails = 0
    for task in Task.objects.filter(semester=semester):
        missing_mails += (
            Tutor.objects.filter(task=task)
            .exclude(id__in=MailTutorTask.objects.filter(task=task).values("tutor_id"))
            .count()
        )

    accepted_tutors = Tutor.objects.filter(semester=semester, status=Tutor.STATUS_ACCEPTED).count()
    waiting_tutors = Tutor.objects.filter(semester=semester, status=Tutor.STATUS_ACTIVE).count()
    return render(
        request,
        "tutors/dashboard.html",
        {
            "subject_counts": count_results,
            "events": events,
            "tasks": tasks,
            "missing_mails": missing_mails,
            "accepted_tutors": accepted_tutors,
            "waiting_tutors": waiting_tutors,
        },
    )
