from django.contrib import admin

from .models import (
    Answer,
    Event,
    MailTutorTask,
    Question,
    Settings,
    SubjectTutorCountAssignment,
    Task,
    Tutor,
    TutorAssignment,
)


@admin.register(Tutor)
class TutorAdmin(admin.ModelAdmin):
    list_display = ["first_name", "last_name", "semester"]
    list_filter = [
        ("semester", admin.RelatedOnlyFieldListFilter),
    ]


admin.site.register(Task)
admin.site.register(Event)
admin.site.register(TutorAssignment)
admin.site.register(Answer)
admin.site.register(Question)
admin.site.register(Settings)
admin.site.register(MailTutorTask)
admin.site.register(SubjectTutorCountAssignment)
