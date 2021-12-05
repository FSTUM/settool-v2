# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
from settool.settings.base_settings import *  # noqa: 401,F403

USE_KEYCLOAK = False

AUTHENTICATION_BACKENDS = ("django.contrib.auth.backends.ModelBackend",)
