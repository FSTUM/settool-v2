import os
import shutil
# the calls in this method are fine, as they are and all input is predefined by django.
from subprocess import call  # nosec
from tempfile import mkdtemp, mkstemp

from django.template.loader import render_to_string


def latex_to_pdf(tex_path, context):
    # In a temporary folder, make a temporary file
    tmp_folder = mkdtemp()
    file, filename = mkstemp(dir=tmp_folder)
    # Pass the TeX template through Django templating engine and into the temp file
    os.write(file, render_to_string(tex_path, context).encode())
    os.close(file)
    # Compile the TeX file with PDFLaTeX
    call(['pdflatex', '-output-directory', tmp_folder, filename])

    # Move resulting PDF to a more permanent location
    with open(f"{filename}.pdf", "rb") as rendered_pdf:
        result = rendered_pdf.read()
    # Remove folder and contained intermediate files
    shutil.rmtree(tmp_folder, ignore_errors=True)
    return result
