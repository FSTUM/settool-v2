from django import template

register = template.Library()


@register.filter
def in_task(requirement, task_requirements):
    return requirement.filter(question__id__in=task_requirements.values("id"))