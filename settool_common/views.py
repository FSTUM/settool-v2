from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.utils.http import is_safe_url
from django.http import HttpResponseRedirect

from .settings import SEMESTER_SESSION_KEY
from .models import Semester

@login_required
def set_semester(request):
    next = request.POST.get('next', request.GET.get('next'))
    if not is_safe_url(url=next, host=request.get_host()):
        next = request.META.get('HTTP_REFERER')
        if not is_safe_url(url=next, host=request.get_host()):
            next = '/'
    response = HttpResponseRedirect(next)
    if request.method == 'POST':
        semester_pk = int(request.POST.get("semester"))
        try:
            Semester.objects.get(pk=semester_pk)
        except Semester.DoesNotExist:
            pass
        else:
            request.session[SEMESTER_SESSION_KEY] = semester_pk
    return response
