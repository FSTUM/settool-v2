import csv
import os
from typing import Any, Dict, List, Union

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet
from django.http import HttpResponse


def download_csv(
    fields: List[str],
    dest: str,
    context: Union[QuerySet[Any], Dict[Any, Any], List[Any]],
) -> HttpResponse:
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"inline; filename={os.path.basename(dest)}"
    writer = csv.writer(response, dialect=csv.excel)
    writer.writerow(fields)

    for obj in context:
        row = []
        for field in fields:
            if hasattr(obj, field):
                row.append(getattr(obj, field))
            else:
                row.append(obj[field])
        writer.writerow(row)

    return response


def produce_field_with_autosubmit(field_class, label, **kwargs):
    tmp = field_class(
        label=label,
        required=False,
        **kwargs,
    )

    tmp.widget.attrs["onchange"] = "document.getElementById('filterform').submit()"
    return tmp


def object_does_exists(klass, semester, **kwargs):
    try:
        klass.objects.get(semester=semester, **kwargs)
    except ObjectDoesNotExist:
        return False
    return True


def get_or_none(klass, *args, **kwargs):
    try:
        return klass.objects.get(*args, **kwargs)
    except klass.DoesNotExist:
        return None
