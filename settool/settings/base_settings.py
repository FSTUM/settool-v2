"""
Django settings for settool project.

Generated by 'django-admin startproject' using Django 1.9.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os
from pathlib import Path
from typing import Optional

from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "CHANGE_ME_CHANGE_ME_CHANGE_ME_CHANGE_ME"  # nosec: this is changed, when deploying

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS: list[str] = []

# Application definition

INSTALLED_APPS = [
    "modeltranslation",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_bootstrap5",
    "bootstrap_datepicker_plus",
    "bootstrap_modal_forms",
    "active_link",
    "django_crontab",
    "django_tex",
    "settool_common",
    "guidedtours",
    "bags",
    "fahrt",
    "tutors",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.gzip.GZipMiddleware",
]

ROOT_URLCONF = "settool.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
    {
        "NAME": "tex",
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "DIRS": ["templates"],
    },
]
LATEX_INTERPRETER = "latexmk -pdf"

WSGI_APPLICATION = "settool.wsgi.application"

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    },
}
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Auth
LOGIN_URL = "/login/"
LOGOUT_URL = "/logout/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "login"
LOGIN_REDIRECT_URL_FAILURE = "/login/failed"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

USE_KEYCLOAK: Optional[bool] = None

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = "en"
LANGUAGES = (
    ("de", _("German")),
    ("en", _("English")),
)
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_L10N = True
LOCALE_PATHS = ["locale"]
MODELTRANSLATION_TRANSLATION_FILES = ("tutors.translation", "settool_common.translation")

BOOTSTRAP4 = {
    "include_jquery": False,
}

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "node_modules"),
    os.path.join(BASE_DIR, "staticfiles"),
]

# Media files (QR-Codes, ...)
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# cronjobs
CRONJOBS = [
    ("0 6 * * *", "settool_common.cron.reminder_cronjob"),  # At 06:00
    ("5 0 * * 0", "settool_common.cron.privacy_cronjob"),  # At 05:00 on Sundays
]
