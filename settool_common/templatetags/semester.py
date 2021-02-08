import datetime

from django import template

from settool_common.models import current_semester
from settool_common.models import get_semester as get_sem
from settool_common.models import Semester

register = template.Library()


@register.simple_tag
def get_available_semesters():
    return Semester.objects.all()


@register.simple_tag(takes_context=True)
def get_semester(context):
    request = context["request"]
    return get_sem(request)


@register.simple_tag
def get_current_semester():
    return current_semester().pk


@register.filter
def next_sunday_after(date):
    return date - datetime.timedelta(date.weekday()) + datetime.timedelta(6)
