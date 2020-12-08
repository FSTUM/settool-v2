from modeltranslation.translator import TranslationOptions
from modeltranslation.translator import translator

from tutors.models import Event
from tutors.models import Question
from tutors.models import Task


class EventTranslationOptions(TranslationOptions):
    fields = ("name", "description", "meeting_point")
    required_languages = ("en", "de")


class TaskTranslationOptions(TranslationOptions):
    fields = ("name", "description", "meeting_point")
    required_languages = ("en", "de")


class QuestionTranslationOptions(TranslationOptions):
    fields = ("question",)
    required_languages = ("en", "de")


translator.register(Event, EventTranslationOptions)
translator.register(Task, TaskTranslationOptions)
translator.register(Question, QuestionTranslationOptions)
