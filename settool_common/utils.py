import os
import shutil
import sys
from subprocess import call
from tempfile import mkdtemp, mkstemp

from django.template.loader import render_to_string

# convert to unicode
if sys.version_info < (3,):
    def u(x):
        # pylint: disable=E0602
        return unicode(x)
else:
    def u(x):
        return str(x)


def latex_to_pdf(tex_path, context):
    # In a temporary folder, make a temporary file
    tmp_folder = mkdtemp()
    os.chdir(tmp_folder)
    texfile, texfilename = mkstemp(dir=tmp_folder)
    # Pass the TeX template through Django templating engine and into the temp file
    os.write(texfile, render_to_string(tex_path, context).encode())
    os.close(texfile)
    # Compile the TeX file with PDFLaTeX
    call(['pdflatex', texfilename])

    with open(texfilename + ".pdf", "rb") as f:
        result = f.read()
    # Move resulting PDF to a more permanent location
    # Remove intermediate files
    os.remove(texfilename)
    os.remove(texfilename + '.aux')
    os.remove(texfilename + '.log')
    try:
        shutil.rmtree(tmp_folder)
    finally:
        return result
