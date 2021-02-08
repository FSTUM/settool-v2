from django.contrib import admin

from .models import Fahrt, LogEntry, Participant

admin.site.register(Participant)
admin.site.register(Fahrt)
admin.site.register(LogEntry)
