from django.contrib import admin

from .models import Status, Tutor, Task, Group, TutorAssignment

admin.site.register(Status)
admin.site.register(Tutor)
admin.site.register(Task)
admin.site.register(Group)
admin.site.register(TutorAssignment)
