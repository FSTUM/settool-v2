from django.contrib import admin

from .models import Semester
from .models import Subject

admin.site.register(Semester)
admin.site.register(Subject)
