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

- Python 3.7
- Python modules listed in `requirements.txt`
- pdflatex (from TeX Live)

Developement needs in addition to those named before
- Python modules listed in `requirements_dev.txt`
- `build-essential` to run the Makefile

# Run for development

By default, Django uses a SQLite database that can be generated using the following command inside the project
directory:

    python3 manage.py migrate

Then a superuser should be created:

    python3 manage.py createsuperuser

This does not set the `fist_name`, so we show the user his `username` instead. If you want your `fist_name` to be shown instead, you have to add your fist Name in the admin pannel. 

Now you can start the webserver for development:

    python3 manage.py runserver

Now visit http://localhost:8000 with your browser.

# Test CI locally

you have three options:
- via the included Makefile
  - run

        make JOB
  
    to execute a job locally.
  - alternatively run
    
        make STAGE
  
    to execute a Stage locally.

- If you want to execute the whole CI (using docker) localy, run
  
      sudo gitlab-runner exec docker JOB
  
  This assumes you have already installed gitlab-runner localy as by gitlab documentation.
  **This option is only nessesary if you run into CI Problems or want to test the CI localy.**

The following Stages are availible:

|**Stage**| **Job**     | **Description**                                                                               |
|---------|-------------|-----------------------------------------------------------------------------------------------|
| test    | run_pytests | Runs all the pytests                                                                          |
| linting | bandit      | Executes [Bandit](https://pypi.org/project/bandit/), a tool that finds common security issues |
| linting | mypy        | Executes [mypy](https://mypy-lang.org/), a tool type checks your code                         |
| linting | pylint      | Executes [Pylint](https://pypi.org/project/pylint/),  a tool type checks your code            |

# pre-commit

Code quality is ensured via various tools bundled in [`pre-commit`](https://github.com/pre-commit/pre-commit/).

You can install `pre-commit`, so it will automatically run on commit:
```console
pre-commit install
```
This will check all files modified by your commit and will prevent the commit if a hook fails. To check all files, you can run
```console
pre-commit run --all-files
```

# Translation

Update the .po files with:

    python3 manage.py makemessages -l de

Then edit the .po files, e.g. `guidedtours/locale/de/LC_MESSAGES/django.po`. Poedit is an excellent GUI for this!

`pre-commit` will automatically create the `.mo`-files for you.
