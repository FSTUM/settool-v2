# Install

It is recommended to use virtualenv:

After cloning the project, you can create a new virtualenv
(assuming you are outside the folder you just cloned)

    python3 -m venv set-tool

Install all the requirements needed for developement and testing using:

    cd set-tool
    . ./bin/activate

    pip3 install -U -r requirements.txt
    pip3 install -U -r requirements_dev.txt

# Dependencies

## Software

 * Python 3
 * pdflatex (from TeX Live)

## Python modules

See dependencies

To update this file, execute:

    pip3 freeze > dependencies

# Run for development

By default, Django uses a SQLite database that can be generated using the
following command inside the project directory:

    python3 manage.py migrate

Then a superuser should be created:

    python3 manage.py createsuperuser

Now you can start the webserver for development:

    python3 manage.py runserver

Now visit http://localhost:8000 with your browser.

# Translation

Update the .po files with:

    python3 manage.py makemessages -l de

Then edit the .po files, e.g. guidedtours/locale/de/LC_MESSAGES/django.po.
poedit is an excellent GUI for this!

Finally, create the .mo files with the new translations:

    python3 manage.py compilemessages

# LICENSE

Copyright (C) 2015  Julian Biendarra, Frederic Naumann, Felix Hartmond,
                    Michael Eder, Sven Hertle

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
