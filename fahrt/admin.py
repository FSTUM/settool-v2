from django.contrib import admin

from .models import Participant, Fahrt, LogEntry

admin.site.register(Participant)
admin.site.register(Fahrt)
admin.site.register(LogEntry)
