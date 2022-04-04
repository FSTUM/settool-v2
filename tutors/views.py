import time
from typing import Any, Optional, Union
from uuid import UUID

from django import http
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.db import IntegrityError
from django.db.models import Count, QuerySet
from django.forms import forms, modelformset_factory
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.template import Context, Template
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django_tex.response import PDFResponse
from django_tex.shortcuts import render_to_pdf

from kalendar.models import BaseDateGroupInstance, Date
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
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    settings = get_object_or_404(Settings, semester=semester)

    if not settings.registration_open:
        return render(
            request,
            "tutors/standalone/tutor_signup/registration_closed.html",
            {
                "start": settings.open_registration,
                "end": settings.close_registration,
            },
        )

    answer_formset, questions_exist = generate_answer_formset(request, semester)
    form = TutorForm(request.POST or None, semester=semester)
    if form.is_valid() and (not questions_exist or answer_formset.is_valid()):
        if settings.mail_registration is None:
            messages.error(
                request,
                _(
                    "We did not configure a mail to send to you in case you registered. Please Contact {mail} and "
                    "tell us about this error. We are very sorry about this inconvenience. To make up for it cute "
                    "cat-images: https://imgur.com/gallery/3OMii",
                ).format(mail=TutorMail.SET_TUTOR),
            )
            return redirect("tutors:tutor_signup")
        try:
            tutor: Tutor = form.save()
        except IntegrityError:
            messages.error(
                request,
                _(
                    "The email {tutor_mail_address} does already exist for the {semester}. "
                    "Did you already sign up, or is the email invalid? "
                    "Please write us a mail at {set_mail_address} instead of trying again.",
                ).format(
                    semester=str(semester),
                    tutor_mail_address=form.cleaned_data["email"],
                    set_mail_address=TutorMail.SET_TUTOR,
                ),
            )
            return redirect("tutors:tutor_signup")

        tutor.log(None, "Signed up")
        save_answer_formset(answer_formset, tutor.id)

        activation_url = request.build_absolute_uri(
            reverse(
                "tutors:tutor_signup_confirm",
                kwargs={
                    "uidb64": urlsafe_base64_encode(force_bytes(tutor.pk)),
                    "token": account_activation_token.make_token(tutor),  # type: ignore
                },
            ),
        )
        if not settings.mail_registration.send_mail_registration(tutor, activation_url):
            messages.error(
                request,
                _("Could not send email. If this error persists send a mail to {mail}").format(mail=TutorMail.SET),
            )
            return redirect("tutors:tutor_signup")
        MailTutorTask.objects.create(tutor=tutor, mail=settings.mail_registration, task=None)
        return redirect("tutors:tutor_signup_confirmation_required")

    context = {
        "semester": semester,
        "answer_formset": answer_formset,
        "questions_exist": questions_exist,
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
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    settings = get_object_or_404(Settings, semester=semester)

    if not settings.registration_open:
        return render(
            request,
            "tutors/standalone/collaborator_signup/registration_closed.html",
            {
                "start": settings.open_registration,
                "end": settings.close_registration,
            },
        )

    answer_formset, questions_exist = generate_answer_formset(request, semester)
    form = CollaboratorForm(request.POST or None, semester=semester)
    if form.is_valid() and (not questions_exist or answer_formset.is_valid()):
        try:
            collaborator: Tutor = form.save(commit=False)
            collaborator.status = Tutor.STATUS_EMPLOYEE
            collaborator.save()
        except IntegrityError:
            messages.error(
                request,
                _(
                    "The email {tutor_mail_address} does already exist for the {semester}. "
                    "Did you already sign up, or is the email invalid? "
                    "Please write us a mail at {set_mail_address} instead of trying again.",
                ).format(
                    semester=str(semester),
                    tutor_mail_address=form.cleaned_data["email"],
                    set_mail_address=TutorMail.SET_TUTOR,
                ),
            )
            return redirect("tutors:collaborator_signup")

        collaborator.log(None, "Signed up")
        save_answer_formset(answer_formset, collaborator.id)
        return redirect("tutors:collaborator_signup_success")

    context = {
        "semester": semester,
        "answer_formset": answer_formset,
        "questions_exist": questions_exist,
        "form": form,
    }
    return render(request, "tutors/standalone/collaborator_signup/signup.html", context)


def generate_answer_formset(request: WSGIRequest, semester: Semester) -> tuple[Any, bool]:
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
        return (
            AnswerFormSet(
                request.POST,
                request.FILES,
                queryset=Answer.objects.none(),
                initial=initial_data,
            ),
            question_count > 0,
        )
    return AnswerFormSet(queryset=Answer.objects.none(), initial=initial_data), question_count > 0


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
        return redirect("tutors:tutor_signup_success")
    return redirect("tutors:tutor_signup_invalid")


@permission_required("tutors.edit_tutors")
def list_participants(request: WSGIRequest, status: str) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))

    if status == "all":
        tutors = Tutor.objects.filter(semester=semester)
    else:
        tutors = Tutor.objects.filter(semester=semester, status=status)
    return render(
        request,
        "tutors/tutor/list.html",
        {
            "tutors": tutors.order_by("created_at"),
            "status": status,
            "questions": Question.objects.filter(semester=semester),
        },
    )


def view_tutor(request: WSGIRequest, uid: UUID) -> HttpResponse:
    tutor = get_object_or_404(Tutor, pk=uid)
    return render(request, "tutors/tutor/view.html", {"tutor": tutor})


@permission_required("tutors.edit_tutors")
def change_tutor_status(request: WSGIRequest, uid: UUID, status: str) -> HttpResponse:
    tutor = get_object_or_404(Tutor, pk=uid)
    form = forms.Form(request.POST or None)

    if form.is_valid() and status in (x for x, _ in Tutor.STATUS_OPTIONS):
        tutor.status = status
        tutor.save()
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
    return http.HttpResponseBadRequest()


@permission_required("tutors.edit_tutors")
def del_tutor(request: WSGIRequest, uid: UUID) -> HttpResponse:
    tutor = get_object_or_404(Tutor, pk=uid)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        tutor.delete()
        messages.success(request, _("Deleted Tutor {tutor}.").format(tutor=tutor))
        return redirect("tutors:list_status_all")

    context = {
        "tutor": tutor,
        "form": form,
    }
    return render(request, "tutors/tutor/delete.html", context)


@permission_required("tutors.edit_tutors")
def edit_tutor(request: WSGIRequest, uid: UUID) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    tutor: Tutor = get_object_or_404(Tutor, pk=uid)

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
            res: Answer = answer.save(commit=False)
            res.tutor_id = tutor.id
            res_question: Optional[Question] = answer.cleaned_data.get("question")
            if res_question is None:
                raise ValueError("Question should never be None")
            res.question_id = res_question.id
            res.save()
        tutor.log(request.user, "Tutor edited")
        messages.success(request, f"Saved Tutor {tutor}.")

        return redirect("tutors:view_tutor", tutor.id)

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
def edit_event(request: WSGIRequest, uid: UUID) -> HttpResponse:
    event = get_object_or_404(Event, pk=uid)

    form = EventAdminForm(request.POST or None, semester=event.semester, instance=event)
    if form.is_valid():
        form.save()
        event.log(request.user, "Event edited")
        messages.success(request, f"Saved Event {event.name}.")

        return redirect("tutors:view_event", event.id)

    return render(
        request,
        "tutors/event/edit.html",
        {
            "form": form,
            "event": event,
        },
    )


@permission_required("tutors.edit_tutors")
def list_event(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    events = Event.sorted_by_semester(semester.id)
    return render(request, "tutors/event/list.html", {"events": events})


@permission_required("tutors.edit_tutors")
def del_event(request: WSGIRequest, uid: UUID) -> HttpResponse:
    event = get_object_or_404(Event, pk=uid)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        event.delete()
        messages.success(request, f"Deleted Event {event.name}.")
        return redirect("tutors:list_event")

    context = {
        "event": event,
        "form": form,
    }
    return render(request, "tutors/event/delete.html", context)


@permission_required("tutors.edit_tutors")
def add_event(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))

    form = EventAdminForm(request.POST or None, semester=semester)
    if form.is_valid():
        event = form.save()
        event.log(None, "Event added")
        messages.success(request, f"Added Event {event.name}.")

        return redirect("tutors:list_event")

    context = {
        "semester": semester,
        "form": form,
    }
    return render(request, "tutors/event/add.html", context)


def view_event(request: WSGIRequest, uid: UUID) -> HttpResponse:
    event = get_object_or_404(Event, pk=uid)
    return render(request, "tutors/event/view.html", {"event": event})


@permission_required("tutors.edit_tutors")
def edit_task(request: WSGIRequest, uid: UUID) -> HttpResponse:
    task = get_object_or_404(Task, pk=uid)

    form = TaskAdminForm(request.POST or None, semester=task.semester, instance=task)
    if form.is_valid():
        form.save()
        task.log(request.user, "Task edited")
        messages.success(request, f"Saved Task {task.name}.")

        return redirect("tutors:view_task", task.id)

    return render(
        request,
        "tutors/task/edit.html",
        {
            "form": form,
            "task": task,
        },
    )


@permission_required("tutors.edit_tutors")
def list_task(request: WSGIRequest) -> HttpResponse:
    tasks = Task.sorted_by_semester(get_semester(request))
    return render(request, "tutors/task/list.html", {"tasks": tasks})


@permission_required("tutors.edit_tutors")
def del_task(request: WSGIRequest, uid: UUID) -> HttpResponse:
    task = get_object_or_404(Task, pk=uid)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        task.delete()
        messages.success(request, f"Deleted Task {task.name}.")
        return redirect("tutors:list_task")

    context = {
        "task": task,
        "form": form,
    }
    return render(request, "tutors/task/delete.html", context)


@permission_required("tutors.edit_tutors")
def add_task(request: WSGIRequest, eid: Optional[UUID] = None) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))

    form = TaskAdminForm(request.POST or None, semester=semester, initial={"event": eid})
    if form.is_valid():
        task = form.save()
        task.log(None, "Task added")
        messages.success(request, f"Added Task {task.name}.")

        return redirect("tutors:list_task")

    context = {
        "semester": semester,
        "form": form,
    }
    return render(request, "tutors/task/add.html", context)


def view_task(request: WSGIRequest, uid: UUID) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    task = get_object_or_404(Task, pk=uid)

    if not request.user.has_perm("tutors.edit_tutors"):
        return render(request, "tutors/task/view.html", {"task": task})

    form = TaskAssignmentForm(request.POST or None, semester=task.semester, instance=task)
    if form.is_valid():
        form.save()
        task.log(request.user, "Task Assignment edited")
        messages.success(request, f"Saved Task Assignment {task.name}.")

    assigned_tutors = task.tutors.all().order_by("last_name")

    paralel_dates: set[Date] = set()
    for test_date in Date.objects.all():
        if not task.associated_meetings:
            raise IntegrityError(f"task {task.id} has no associated_meetings")
        for orig_date in task.associated_meetings.date_set.all():
            if not orig_date.intersects(test_date):
                paralel_dates.add(test_date)
    paralel_tasks = Task.objects.filter(associated_meetings__date__in=paralel_dates)
    parallel_task_tutors = Tutor.objects.filter(tutorassignment__task__in=paralel_tasks)
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
def list_requirements(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    questions = Question.objects.filter(semester=semester)
    return render(request, "tutors/requirement/list.html", {"requirements": questions})


@permission_required("tutors.edit_tutors")
def view_requirement(request: WSGIRequest, uid: UUID) -> HttpResponse:
    question = get_object_or_404(Question, pk=uid)
    return render(request, "tutors/requirement/view.html", {"requirement": question})


@permission_required("tutors.edit_tutors")
def add_requirement(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))

    form = RequirementAdminForm(request.POST or None, semester=semester)
    if form.is_valid():
        question = form.save()
        question.log(None, "Requirement added")
        messages.success(request, f"Added Requirement {question.question}.")

        return redirect("tutors:list_requirements")

    context = {
        "semester": semester,
        "form": form,
    }
    return render(request, "tutors/requirement/add.html", context)


@permission_required("tutors.edit_tutors")
def edit_requirement(request: WSGIRequest, uid: UUID) -> HttpResponse:
    question = get_object_or_404(Question, pk=uid)

    form = RequirementAdminForm(request.POST or None, semester=question.semester, instance=question)
    if form.is_valid():
        form.save()
        question.log(request.user, "Question edited")
        messages.success(request, f"Saved Task {question.question}.")

        return redirect("tutors:view_requirement", question.id)

    return render(
        request,
        "tutors/requirement/edit.html",
        {
            "form": form,
            "requirement": question,
        },
    )


@permission_required("tutors.edit_tutors")
def del_requirement(request: WSGIRequest, uid: UUID) -> HttpResponse:
    question = get_object_or_404(Question, pk=uid)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        question.delete()
        messages.success(request, f"Deleted Question {question.question}.")
        return redirect("tutors:list_requirements")

    context = {
        "requirement": question,
        "form": form,
    }
    return render(request, "tutors/requirement/delete.html", context)


@permission_required("tutors.edit_tutors")
def task_mail(request: WSGIRequest, uid: UUID, mail_pk: Optional[int] = None) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    settings = get_object_or_404(Settings, semester=semester)
    task = get_object_or_404(Task, pk=uid)

    if mail_pk is None:
        mail = settings.mail_task
        if mail is None:
            messages.error(request, _("The mail_task is not set in the settings. Please choose one option to continue"))
            return redirect("tutors:general_settings")
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
        return redirect("tutors:list_task")
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
def export(request: WSGIRequest, file_type: str, status: str = "all") -> Union[HttpResponse, PDFResponse]:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))

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
def export_task(request: WSGIRequest, file_type: str, uid: UUID) -> PDFResponse:
    task = get_object_or_404(Task, pk=uid)
    tutors = task.tutors.order_by("last_name", "first_name")

    filename = f"task_{task.id}_{time.strftime('%Y%m%d-%H%M')}"
    if file_type == "pdf":
        return render_to_pdf(request, "tutors/tex/task.tex", {"task": task, "tutors": tutors}, f"{filename}.pdf")
    raise Http404


@permission_required("tutors.edit_tutors")
def general_settings(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
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

        return redirect("tutors:general_settings")

    return render(
        request,
        "tutors/settings/general.html",
        {
            "form": form,
        },
    )


@permission_required("tutors.edit_tutors")
def tutor_settings(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))

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

        return redirect("tutors:tutor_settings")

    return render(
        request,
        "tutors/settings/tutors.html",
        {
            "form_set": answer_formset,
        },
    )


@permission_required("tutors.edit_tutors")
def send_mail(
    request: WSGIRequest,
    status: str = "all",
    mail_pk: Optional[int] = None,
    uid: Optional[UUID] = None,
) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    settings = get_object_or_404(Settings, semester=semester)
    template = default_tutor_mail(settings, status, mail_pk)

    if template is None:
        raise Http404

    if uid is None:
        if status == "all":
            tutors: QuerySet[Tutor] = Tutor.objects.filter(semester=semester)
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
        listed_tutors = list(tutors)
        mail_template = form.cleaned_data["mail_template"]

        send_email_to_all_tutors(mail_template, listed_tutors, request)

        return redirect(f"tutors:list_status_{status}")

    context: dict[str, Any] = {
        "from": template.sender,
        "subject": subject,
        "body": body,
        "form": form,
        "status": status,
        "template": template,
        "tutor": tutor,
    }
    return render(request, "tutors/tutor/mail.html", context)


def extract_tutor_data() -> dict[str, str]:
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
    tutors: list[Tutor],
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


def _gen_messages_assignments_wish_counter(
    request: WSGIRequest,
    assignment_wishes: QuerySet[SubjectTutorCountAssignment],
    tutors_active: QuerySet[Tutor],
    tutors_accepted_cnt: dict[int, int],
) -> bool:
    warnings: list[str] = []
    set_subjects: set[int] = {
        assignment_wish.subject.pk
        for assignment_wish in assignment_wishes
        if assignment_wish.wanted is not None and assignment_wish.waitlist is not None
    }
    subjects: set[int] = {subject.pk for subject in Subject.objects.all()}
    unset_subjects: set[int] = subjects.difference(set_subjects)
    assignment_wish_counter: SubjectTutorCountAssignment
    for assignment_wish_counter in assignment_wishes:
        subject: Subject = assignment_wish_counter.subject
        if (
            subject.pk in unset_subjects
            or assignment_wish_counter.wanted is None  # only for mypy
            or assignment_wish_counter.waitlist is None  # only for mypy
        ):
            continue
        wanted, waitlist = assignment_wish_counter.wanted, assignment_wish_counter.waitlist

        active_cnt: int = tutors_active.filter(subject=subject).count()
        accepted_cnt: int = tutors_accepted_cnt.get(subject.pk, 0)
        # low tier error
        if wanted < accepted_cnt:
            warnings.append(
                _(
                    "The subject '{subject}' has more people already accepted then are specified in the wanted-list.",
                ).format(subject=subject),
            )
            # case that wanted or wait-list are zero
        if wanted == 0 and active_cnt:
            warnings.append(
                _(
                    "The subject '{subject}' wanted-list is zero. "
                    "This is subject will not be accepted, even though Tutors for this subject exist..",
                ).format(
                    subject=subject,
                ),
            )
        if waitlist == 0 and wanted < active_cnt + accepted_cnt:
            warnings.append(
                _(
                    "The subject '{subject}' wait-list is zero and there are more tutors that could fit on this "
                    "wait-list.",
                ).format(
                    subject=subject,
                ),
            )
    if warnings:
        warnings.append(_("Please make sure that all warnings above are intentional"))
        warnings_string = mark_safe("</br>".join(warnings))  # nosec: fully defined
        messages.warning(request, warnings_string)
    if unset_subjects:
        unset_subjects_list: list[Subject] = [Subject.objects.get(pk=pk) for pk in unset_subjects]
        unset_subjects_str: list[str] = [
            _("The subject '{subject}' has unset fields").format(subject=subject) for subject in unset_subjects_list
        ]
        unset_subjects_str.append(_("Make sure, that all these Subjects have all values configured"))

        errors_string = mark_safe("</br>".join(unset_subjects_str))  # nosec: fully defined
        messages.error(request, errors_string)
        messages.error(
            request,
            _(
                "Having errors is unacceptable. "
                "You have been redirected to the settings to fix them. "
                "Non-batch operations dont need as explicit configuration.",
            ),
        )
    return bool(unset_subjects)


@permission_required("tutors.edit_tutors")
def batch_accept(request: WSGIRequest) -> HttpResponse:
    semester, tutors_active, tutors_accepted_cnt, assignment_wishes, errors = _gather_batch_parameters(request)
    if errors:
        return redirect("tutors:general_settings")

    tutor_ids: list[UUID] = []
    to_be_accepted: dict[Subject, list[Tutor]] = {}

    assignment_wish: SubjectTutorCountAssignment
    for assignment_wish in assignment_wishes:
        subject, wanted, _ = assignment_wish.save_unpack()
        active_tutors: QuerySet[Tutor] = tutors_active.filter(subject=subject)
        accepted_count: int = tutors_accepted_cnt.get(subject.pk, 0)

        if wanted > accepted_count:
            need: int = wanted - accepted_count
            tutor: Tutor
            for tutor in active_tutors.order_by("created_at")[:need]:
                tutor_ids.append(tutor.id)

                if subject not in to_be_accepted:
                    to_be_accepted[subject] = []
                to_be_accepted[subject].append(tutor)

    form = TutorAcceptAdminForm(
        request.POST or None,
        tutors=Tutor.objects.filter(id__in=tutor_ids),
        semester=semester,
    )
    if form.is_valid():
        tutors: list[Tutor] = form.cleaned_data["tutors"]
        accepted_tutor: Tutor
        for accepted_tutor in tutors:
            accepted_tutor.status = Tutor.STATUS_ACCEPTED
            accepted_tutor.save()

        return redirect("tutors:list_status_active")

    context = {
        "to_be_accepted": to_be_accepted,
        "form": form,
    }
    return render(request, "tutors/tutor/batch_accept.html", context)


@permission_required("tutors.edit_tutors")
def batch_decline(request: WSGIRequest) -> HttpResponse:
    semester, tutors_active, tutors_accepted_cnt, assignment_wishes, errors = _gather_batch_parameters(request)
    if errors:
        return redirect("tutors:general_settings")

    tutor_ids: list[UUID] = []
    to_be_declined: dict[Subject, list[Tutor]] = {}

    assignment_wish: SubjectTutorCountAssignment
    for assignment_wish in assignment_wishes:
        subject, wanted, waitlist = assignment_wish.save_unpack()

        active_tutors: QuerySet[Tutor] = tutors_active.filter(subject=subject)
        accepted_count: int = tutors_accepted_cnt.get(subject.pk, 0)

        keep: int = max(wanted - accepted_count + waitlist, 0)

        for tutor in active_tutors.order_by("created_at")[keep:]:
            tutor_ids.append(tutor.id)

            if subject not in to_be_declined:
                to_be_declined[subject] = []
            to_be_declined[subject].append(tutor)

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

        return redirect("tutors:list_status_active")

    context = {
        "to_be_declined": to_be_declined,
        "form": form,
    }
    return render(request, "tutors/tutor/batch_decline.html", context)


def _gather_batch_parameters(
    request: WSGIRequest,
) -> tuple[Semester, QuerySet[Tutor], dict[int, int], QuerySet[SubjectTutorCountAssignment], bool]:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))
    # tutor specific parameters
    all_tutors: QuerySet[Tutor] = Tutor.objects.filter(semester=semester)
    tutors_active: QuerySet[Tutor] = all_tutors.filter(status=Tutor.STATUS_ACTIVE)
    tutors_accepted_cnt: dict[int, int] = {
        tutor_acc_count["subject"]: tutor_acc_count["subject_count"]
        for tutor_acc_count in all_tutors.filter(status=Tutor.STATUS_ACCEPTED)
        .values("subject")
        .annotate(subject_count=Count("subject"))
        .all()
    }
    # preferences
    assignment_wishes: QuerySet[SubjectTutorCountAssignment] = SubjectTutorCountAssignment.objects.filter(
        semester=semester,
    )
    # check if assignment_wishes is valid. shows warnings and errors
    errors: bool = _gen_messages_assignments_wish_counter(
        request,
        assignment_wishes,
        tutors_active,
        tutors_accepted_cnt,
    )
    messages.info(request, _("Batch actions do not send mails. They only change the status of the students."))
    return semester, tutors_active, tutors_accepted_cnt, assignment_wishes, errors


def get_first_future_five(cls: type[BaseDateGroupInstance], semester_id: int) -> list[type[BaseDateGroupInstance]]:
    sorted_instances: list[type[BaseDateGroupInstance]] = cls.sorted_by_semester(semester_id)

    future_instances = []
    for inst in sorted_instances:
        if inst.last_datetime and inst.last_datetime < timezone.now():  # type:ignore
            future_instances.append(inst)
        if len(future_instances) == 5:
            break
    return future_instances


@permission_required("tutors.edit_tutors")
def dashboard(request: WSGIRequest) -> HttpResponse:
    semester: Semester = get_object_or_404(Semester, pk=get_semester(request))

    assignments_wish_counter: QuerySet[SubjectTutorCountAssignment]
    assignments_wish_counter = SubjectTutorCountAssignment.objects.filter(semester=semester)
    count_results = {}
    for assignment_wish_counter in assignments_wish_counter:
        counts_tutors: dict[str, int] = Tutor.objects.filter(
            semester=semester,
            subject=assignment_wish_counter.subject,
            status=Tutor.STATUS_ACCEPTED,
        ).aggregate(total=Count("subject"))
        count_results[assignment_wish_counter.subject] = (
            counts_tutors["total"] or 0,
            assignment_wish_counter.wanted,
        )

    first_future_five_events: list[type[BaseDateGroupInstance]] = get_first_future_five(Event, semester.id)
    first_future_five_tasks: list[type[BaseDateGroupInstance]] = get_first_future_five(Task, semester.id)

    missing_mails = 0
    task: Task
    for task in Task.objects.filter(semester=semester):
        missing_mails += (
            Tutor.objects.filter(tutorassignment__task=task)
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
            "first_future_five_events": first_future_five_events,
            "first_future_five_tasks": first_future_five_tasks,
            "missing_mails": missing_mails,
            "accepted_tutors": accepted_tutors,
            "waiting_tutors": waiting_tutors,
        },
    )
