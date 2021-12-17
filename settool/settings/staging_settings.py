# flake8: noqa
# pylint: skip-file
# type: ignore

import logging.config
import os

USE_KEYCLOAK = os.getenv("USE_KEYCLOAK", "False") == "True"
if USE_KEYCLOAK:
    from settool.settings.keycloak_settings import *

    OIDC_RP_CLIENT_ID = os.environ["OIDC_RP_CLIENT_ID"]
    OIDC_RP_CLIENT_SECRET = os.environ["OIDC_RP_CLIENT_SECRET"]
else:
    from settool.settings.dev_settings import *

DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",")

WSGI_APPLICATION = "settool.staging_wsgi.application"

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
# generate your own secret key using
# import random, string
# print("".join(random.choice(string.printable) for _ in range(50)))

# staticfiles
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# logging
LOGGING_CONFIG = None
LOGLEVEL = os.getenv("DJANGO_LOGLEVEL", "info").upper()
logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "console": {
                "format": "%(asctime)s %(levelname)s "
                "[%(name)s:%(lineno)s] "
                "%(module)s %(process)d %(thread)d %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "console",
            },
        },
        "loggers": {
            "": {
                "level": LOGLEVEL,
                "handlers": ["console"],
            },
        },
    },
)
