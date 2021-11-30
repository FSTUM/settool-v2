from django.contrib import admin

from .models import AnonymisationLog, Semester, Subject

admin.site.register(AnonymisationLog)
admin.site.register(Semester)
admin.site.register(Subject)
