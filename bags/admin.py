from django.contrib import admin

from .models import Company
from .models import Mail

admin.site.register(Company)
admin.site.register(Mail)
