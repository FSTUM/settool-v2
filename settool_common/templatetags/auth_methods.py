from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def get_keycloak_status():
    return settings.USE_KEYCLOAK
