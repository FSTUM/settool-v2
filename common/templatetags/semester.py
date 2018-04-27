from django import template

from common.models import Semester, current_semester, get_semester as get_sem

register = template.Library()


@register.simple_tag
def get_available_semesters():
    return Semester.objects.all()


@register.simple_tag(takes_context=True)
def get_semester(context):
    request = context['request']
    return get_sem(request)


@register.simple_tag
def get_current_semester():
    return current_semester().pk
