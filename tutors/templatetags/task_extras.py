from django import template

from tutors.models import Tutor, MailTutorTask

register = template.Library()


@register.filter
def in_task(requirement, task_requirements):
    return requirement.filter(question__id__in=task_requirements.values("id"))


@register.simple_tag
def mail_task_count(task):
    return Tutor.objects.filter(task=task).exclude(id__in=MailTutorTask.objects.filter(task=task).values(
        "tutor_id")).count()
