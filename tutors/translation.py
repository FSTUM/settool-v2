from modeltranslation.translator import TranslationOptions, translator

from tutors.models import Event, Location, Question, Task


class LocationTranslationOptions(TranslationOptions):
    fields = ("shortname", "address")
    required_languages = ("en", "de")


class EventTranslationOptions(TranslationOptions):
    fields = ("name", "description")
    required_languages = ("en", "de")


class TaskTranslationOptions(TranslationOptions):
    fields = ("name", "description")
    required_languages = ("en", "de")


class QuestionTranslationOptions(TranslationOptions):
    fields = ("question",)
    required_languages = ("en", "de")


translator.register(Location, LocationTranslationOptions)
translator.register(Event, EventTranslationOptions)
translator.register(Task, TaskTranslationOptions)
translator.register(Question, QuestionTranslationOptions)
