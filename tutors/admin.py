from django.contrib import admin

from .models import (Status, Tutor, Task, Event, TutorAssignment, Answer,
                     Question, Requirement, Registration)

admin.site.register(Status)
admin.site.register(Tutor)
admin.site.register(Task)
admin.site.register(Event)
admin.site.register(TutorAssignment)
admin.site.register(Answer)
admin.site.register(Question)
admin.site.register(Requirement)
admin.site.register(Registration)
