import os
import shutil
from subprocess import call  # nosec: calls are only local and input is templated
from tempfile import mkdtemp
from tempfile import mkstemp

from django.template.loader import render_to_string


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
    return result
