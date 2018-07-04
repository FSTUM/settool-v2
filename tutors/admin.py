from django.contrib import admin

from .models import (Tutor, Task, Event, TutorAssignment, Answer,
                     Question, Settings, MailTutorTask, SubjectTutorCountAssignment)

admin.site.register(Tutor)
admin.site.register(Task)
admin.site.register(Event)
admin.site.register(TutorAssignment)
admin.site.register(Answer)
admin.site.register(Question)
admin.site.register(Settings)
admin.site.register(MailTutorTask)
admin.site.register(SubjectTutorCountAssignment)
