# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
from settool.settings.base_settings import *  # noqa: 401,F403

USE_KEYCLOAK = False

AUTHENTICATION_BACKENDS = ("django.contrib.auth.backends.ModelBackend",)

# sample database configuration to test for differences in prod
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "postgres",
        "USER": "postgres",
        "PASSWORD": "password",
        "HOST": "localhost",
        "PORT": "5432",
    },
}
