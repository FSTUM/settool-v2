from modeltranslation.translator import translator, TranslationOptions

from tutors.models import Event, Task, Question, Answer


class EventTranslationOptions(TranslationOptions):
    fields = ('name', 'description', 'meeting_point',)
    required_languages = ('en', 'de')


class TaskTranslationOptions(TranslationOptions):
    fields = ('name', 'description', 'meeting_point',)
    required_languages = ('en', 'de')


class QuestionTranslationOptions(TranslationOptions):
    fields = ('question',)
    required_languages = ('en', 'de')

translator.register(Event, EventTranslationOptions)
translator.register(Task, TaskTranslationOptions)
translator.register(Question, QuestionTranslationOptions)
