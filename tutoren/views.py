from django.contrib.auth.decorators import permission_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from common.models import get_semester, Semester
from tutoren.forms import TutorenForm, TutorenAdminForm
from tutoren.models import Tutor, Status
from tutoren.tokens import account_activation_token


def tutoren_signup(request):
    sem = get_semester(request)
    semester = get_object_or_404(Semester, pk=sem)

    # try:
    #     fahrt = semester.fahrt
    # except ObjectDoesNotExist:
    #     registration_open = False
    # else:
    #     registration_open = fahrt.registration_open

    registration_open = True

    if not registration_open:
        return render(request, 'tutoren/registration_closed.html', {})

    form = TutorenForm(request.POST or None, semester=semester)
    if form.is_valid():
        tutor = form.save()
        tutor.log(None, "Signed up")

        mail_subject = 'Confirm your SET Tutor application.'
        message = render_to_string('tutoren/signup_confirm.html', {
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

        return redirect('tutoren_signup_confirmation_required')

    context = {'semester': semester,
               'form': form}
    return render(request, 'tutoren/signup.html', context)


def tutoren_signup_success(request):
    return render(request, 'tutoren/success.html')


def tutoren_signup_invalid(request):
    return render(request, 'tutoren/invalid.html')


def tutoren_signup_confirmation_required(request):
    return render(request, 'tutoren/confirmation_required.html')


def tutoren_signup_confirm(request, uidb64, token):
    uid = force_text(urlsafe_base64_decode(uidb64))
    tutor = get_object_or_404(Tutor, pk=uid)

    if account_activation_token.check_token(tutor, token):
        tutor.status = Status.objects.get(key="active")
        tutor.save()
        return redirect('tutoren_signup_success')
    else:
        return redirect('tutoren_signup_invalid')


@permission_required('tutoren.edit_tutors')
def tutoren_list(request, status=None):
    if status is None:
        tutors = Tutor.objects.all()
    else:
        tutors = Tutor.objects.filter(status__key=status)
    return render(request, 'tutoren/list_tutors.html', {'tutors': tutors})


def tutoren_view(request, uid):
    tutor = get_object_or_404(Tutor, pk=uid)
    return render(request, 'tutoren/view_tutor.html', {'tutor': tutor})


@permission_required('tutoren.edit_tutors')
def tutoren_accept(request, uid):
    tutor = get_object_or_404(Tutor, pk=uid)
    tutor.status = Status.objects.get(key='accepted')
    tutor.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


@permission_required('tutoren.edit_tutors')
def tutoren_decline(request, uid):
    tutor = get_object_or_404(Tutor, pk=uid)
    tutor.status = Status.objects.get(key='declined')
    tutor.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


@permission_required('tutoren.edit_tutors')
def tutoren_delete(request, uid):
    tutor = get_object_or_404(Tutor, pk=uid)
    tutor.delete()
    return redirect("tutoren_list")


@permission_required('tutoren.edit_tutors')
def tutoren_edit(request, uid):
    tutor = get_object_or_404(Tutor, pk=uid)

    form = TutorenAdminForm(request.POST or None, semester=tutor.semester, instance=tutor)
    if form.is_valid():
        form.save()
        tutor.log(request.user, "Tutor edited")

        return redirect('tutoren_view', tutor.id)

    return render(request, 'tutoren/edit_tutor.html', {
        'form': form,
        'tutor': tutor,
    })
