# Scope:

-   [x] manage SET-Fahrt
-   [x] manage SET-Bags
-   [x] manage SET-Guidedtours
-   [x] manage SET-Tutors/Collaborators
-   [ ] manage tasks and dates
-   IO
    -   [x] manage and send tremplated Mails
    -   [x] send reminders
    -   [x] generate (pretty) PDF-Documents
    -   [x] export to CSV

# UI-Samples:

## Base-page for logged-in users

![Base-page](https://user-images.githubusercontent.com/26258709/113455027-e2770700-9409-11eb-8627-e6e0979bffe4.gif)

## Dashboards

![Dashboard 1](https://user-images.githubusercontent.com/26258709/113454429-8069d200-9408-11eb-88fa-9e83151ef449.png)
![Dashboard 2](https://user-images.githubusercontent.com/26258709/113454431-819aff00-9408-11eb-8b0b-04841c629323.png)
![Dashboard 3](https://user-images.githubusercontent.com/26258709/113454434-82339580-9408-11eb-9205-55e0f53335e4.png)

## Management views

![Management view 1](https://user-images.githubusercontent.com/26258709/113455288-895ba300-940a-11eb-9a48-4c613eda2276.png)
![Management view 2](https://user-images.githubusercontent.com/26258709/113455290-89f43980-940a-11eb-8f1a-4bcd8f6ba2be.png)

## Sign up

![Sign-up 1](https://user-images.githubusercontent.com/26258709/113455502-13a40700-940b-11eb-8e31-ba6eab56cba4.png)

# Installation

1. Install system dependencies

```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv texlive-base texlive-lang-german texlive-fonts-recommended texlive-latex-extra latexmk
```

2. Install python-dependencies in an virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

# Development

1. Install additional dependencies after you installed the dependencies listed in [Installation](#installation)

```bash
sudo apt-get install -y gettext npm
python3 -m pip install -r requirements_dev.txt
```

2. Create the SQLite-database by running the following command inside the project directory:

```bash
python3 manage.py migrate
```

3. Create an admin-account by running the following command inside the project directory:

```bash
python3 manage.py createsuperuser
```

Note that this doesn't set the `fist_name`, thus the `username` is shown on the website. If you want your `fist_name` to
be shown instead, you have to add your fist name in the admin interface.

4. Start the local webserver

```bash
python3 manage.py runserver
```

    You can now visist http://localhost:8000/ in your browser

## pre-commit

Code quality is ensured via various tools bundled in [`pre-commit`](https://github.com/pre-commit/pre-commit/).

You can install `pre-commit`, so it will automatically run on every commit:

```bash
pre-commit install
```

This will check all files modified by your commit and will prevent the commit if a hook fails. To check all files, you
can run

```bash
pre-commit run --all-files
```

This will also be run by CI if you push to the repository.

## Sample-Data/ "Fixtures"

you can generate example-data (overrides every model with data that looks partially plausible, but is clearly not
production-data)
by opening the django shell using:

```shell
python3 manage.py shell
```

In the shell type

```python
import settool_common.fixtures.showroom_fixture

settool_common.fixtures.showroom_fixture.showroom_fixture_state()
```

This operation might take a few seconds. Don't worry.

## Adding Depenencies

If you want to add a dependency that is in `pip` add it to the appropriate `requirements`-file.  
If you want to add a dependency that is in `npm` run `npm i DEPENDENCY`. **Make shure that you do only commit the
nessesary files to git.**

# Translation

1. Update the `.po`-files with

```bash
python manage.py makemessages -a
```

2. Edit the `.po`-file. [Poedit](https://poedit.net) is an excellent GUI for this!

    In the Settings please change:

    |        Setting | to value |
    | -------------: | -------- |
    |           name | `$NAME`  |
    |          email | `$EMAIL` |
    |   Line endings | `Unix`   |
    |        Wrap at | `120`    |
    | check-spelling | `True`   |

3. Edit the `.po`-files, e.g. `guidedtours/locale/de/LC_MESSAGES/django.po`.

Note that `pre-commit` will automatically compile the translations for you.

# Staging

A staging environment is offered at `set.frank.elsinga.de`  
The username is `password`  
The password is `username`

## Building and running the dockerfile for local developement

1. you need to save your enveronmment variables in an `.env`-file.
   The further guide assumes content simmilar to the following in `staging/.env`.

```
DJANGO_DEBUG="True"
DJANGO_SECRET_KEY="CHOOSE_A_SAVE_PASSWORD"
DJANGO_ALLOWED_HOSTS="0.0.0.0,localhost,127.0.0.1"
```

2. Build the dockerfile

```
docker build -t settool-staging:v1 .
```

3. Run the Dockerfile

```
docker run --env-file staging/.env -p 8080:8000 settool-staging:v1
```

The Staging instance is now availibe at [`127.0.0.1:8080`](http://127.0.0.1:8080/) and is pushed to the Github Container Registry for convinience.
