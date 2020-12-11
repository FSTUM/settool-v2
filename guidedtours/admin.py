from django.contrib import admin

from .models import Participant
from .models import Tour

admin.site.register(Tour)
admin.site.register(Participant)
