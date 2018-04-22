from django.contrib import admin

from .models import (Status, Tutor, Task, Group, TutorAssignment, Answer,
                     Question, Requirement, Registration)

admin.site.register(Status)
admin.site.register(Tutor)
admin.site.register(Task)
admin.site.register(Group)
admin.site.register(TutorAssignment)
admin.site.register(Answer)
admin.site.register(Question)
admin.site.register(Requirement)
admin.site.register(Registration)
