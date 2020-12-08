from django.contrib.auth.decorators import login_required, permission_required
from django.forms import forms
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.http import is_safe_url

from settool_common.forms import MailForm
from .models import Semester, get_semester, Mail
from .settings import SEMESTER_SESSION_KEY


@login_required
def set_semester(request):
    redirect_url = request.POST.get('next', request.GET.get('next'))
    if not is_safe_url(url=redirect_url, allowed_hosts=request.get_host()):
        redirect_url = request.META.get('HTTP_REFERER')
        if not is_safe_url(url=redirect_url, allowed_hosts=request.get_host()):
            redirect_url = '/'
    response = HttpResponseRedirect(redirect_url)
    if request.method == 'POST':
        semester_pk = int(request.POST.get("semester"))
        try:
            Semester.objects.get(pk=semester_pk)
        except Semester.DoesNotExist:
            pass
        else:
            request.session[SEMESTER_SESSION_KEY] = semester_pk
    return response


@permission_required('set.mail')
def mail_list(request):
    semester = get_object_or_404(Semester, pk=get_semester(request))
    mails = Mail.objects.filter(semester=semester)

    context = {'mails': mails}
    return render(request, 'settool_common/settings/list_email_templates.html', context)


@permission_required('set.mail')
def mail_view(request, pk):
    mail = Mail.objects.get(pk=pk)

    context = {
        'mail': mail,
    }
    return render(request, 'settool_common/settings/email_details.html', context)


@permission_required('set.mail')
def mail_add(request):
    semester = get_object_or_404(Semester, pk=get_semester(request))

    form = MailForm(request.POST or None, semester=semester)
    if form.is_valid():
        form.save()
        return redirect('mail_list')

    context = {'form': form}
    return render(request, 'settool_common/settings/add_email.html', context)


@permission_required('set.mail')
def mail_edit(request, pk):
    mail = get_object_or_404(Mail, pk=pk)

    form = MailForm(request.POST or None, semester=mail.semester, instance=mail)
    if form.is_valid():
        form.save()
        return redirect('mail_list')

    context = {
        'form': form,
        'mail': mail,
    }
    return render(request, 'settool_common/settings/edit_email.html', context)


@permission_required('set.mail')
def mail_delete(request, pk):
    mail = get_object_or_404(Mail, pk=pk)

    form = forms.Form(request.POST or None)
    if form.is_valid():
        mail.delete()
        return redirect('mail_list')

    context = {
        'mail': mail,
        'form': form
    }
    return render(request, 'settool_common/settings/delete_email.html', context)


@permission_required('set.mail')
def mail_send(request, pk):
    mail = get_object_or_404(Mail, pk=pk)
    selected_participants = request.session['selected_participants']
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)
    participants = semester.fahrt_participant.filter(
        id__in=selected_participants).order_by("surname")

    subject, text, from_email = mail.get_mail(request)

    form = forms.Form(request.POST or None)
    failed_participants = []
    if form.is_valid():
        for p in participants:
            success = mail.send_mail(request, p)
            if success:
                p.log(request.user, f"Mail '{mail}' sent")
            else:
                failed_participants.append(p)
        if not failed_participants:
            return redirect('mail_list')

    context = {
        'participants': participants,
        'failed_participants': failed_participants,
        'subject': subject,
        'text': text,
        'from_email': from_email,
        'form': form,
    }

    if failed_participants:
        return render(request, 'settool_common/mail/send_email_failure.html', context)
    return render(request, 'settool_common/mail/send_email_confirmation.html', context)