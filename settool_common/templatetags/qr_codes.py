from django import template
from django.urls import reverse

from settool_common.models import QRCode

register = template.Library()


@register.simple_tag(takes_context=True)
def generate_qr_code_url(context, value):
    request = context["request"]
    full_url = f"{request.scheme}://set.mpi.fs.tum.de{reverse(value)}"
    return QRCode.objects.get_or_create(content=full_url)[0].qr_code.url
