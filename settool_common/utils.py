import os
import shutil
from subprocess import call  # nosec: calls are only local and input is templated
from tempfile import mkdtemp
from tempfile import mkstemp

from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.test.client import Client

from settool_common.settings import SEMESTER_SESSION_KEY


def latex_to_pdf(tex_path, context):
    # In a temporary folder, make a temporary file
    tmp_folder = mkdtemp()
    file, filename = mkstemp(dir=tmp_folder)
    # Pass the TeX template through Django templating engine and into the temp file
    os.write(file, render_to_string(tex_path, context).encode())
    os.close(file)
    # Compile the TeX file with PDFLaTeX
    call(["pdflatex", "-output-directory", tmp_folder, filename])

    # Move resulting PDF to a more permanent location
    with open(f"{filename}.pdf", "rb") as rendered_pdf:
        result = rendered_pdf.read()
    # Remove folder and contained intermediate files
    shutil.rmtree(tmp_folder, ignore_errors=True)
    return result  # noqa: R504


def get_mocked_logged_in_client():
    client = Client()

    user = get_user_model().objects.create_user(  # nosec: this is a unittest
        username="testuser",
        password="12345",
        is_superuser=True,
    )
    client.force_login(user)
    client.session[SEMESTER_SESSION_KEY] = 2  # pk=2 ^= SS 21
    client.session.save()
    return client
