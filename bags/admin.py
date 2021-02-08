from django.contrib import admin

from .models import BagMail
from .models import Company

admin.site.register(Company)
admin.site.register(BagMail)
