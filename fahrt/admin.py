from django.contrib import admin

from .models import Fahrt
from .models import LogEntry
from .models import Participant

admin.site.register(Participant)
admin.site.register(Fahrt)
admin.site.register(LogEntry)
