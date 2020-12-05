# Install

First make shure that all the requirements are met
    
    sudo apt-get update && sudo apt-get install -y build-essential
    pip3 install virtualenv

It is recommended to use virtualenv.
After cloning the project, you can create the new virtualenv by

    virtualenv -q .venv

Install all the requirements needed for developement and testing using:

    source .venv/bin/activate

    pip3 install -U -r requirements.txt
    pip3 install -U -r requirements_dev.txt
  
# Dependencies

- Python 3
- Python modules listed in `requirements.txt`
- pdflatex (from TeX Live)

Developement needs in addition to those named before
- Python modules listed in `requirements_dev.txt`
- build-essential

# Run for development

By default, Django uses a SQLite database that can be generated using the following command inside the project
directory:

    python3 manage.py migrate

Then a superuser should be created:

    python3 manage.py createsuperuser --username=YourName

Now you can start the webserver for development:

    python3 manage.py runserver

Now visit http://localhost:8000 with your browser.

# Translation

Update the .po files with:

    python3 manage.py makemessages -l de

Then edit the .po files, e.g. `guidedtours/locale/de/LC_MESSAGES/django.po`. Poedit is an excellent GUI for this!

Finally, create the .mo files with the new translations:

    python3 manage.py compilemessages
