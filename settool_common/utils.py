import os
import shutil
from subprocess import call
from tempfile import mkdtemp, mkstemp

from django.template.loader import render_to_string


def latex_to_pdf(tex_path, context):
    # In a temporary folder, make a temporary file
    tmp_folder = mkdtemp()
    texfile, texfilename = mkstemp(dir=tmp_folder)
    # Pass the TeX template through Django templating engine and into the temp file
    os.write(texfile, render_to_string(tex_path, context).encode())
    os.close(texfile)
    # Compile the TeX file with PDFLaTeX
    call(['pdflatex', '-output-directory', tmp_folder, texfilename])

    with open(texfilename + ".pdf", "rb") as f:
        result = f.read()
    # Move resulting PDF to a more permanent location
    # Remove intermediate files
    os.remove(texfilename)
    os.remove(texfilename + '.aux')
    os.remove(texfilename + '.log')

    shutil.rmtree(tmp_folder, ignore_errors=True)
    return result
