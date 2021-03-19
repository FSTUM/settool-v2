from modeltranslation.translator import TranslationOptions, translator

from settool_common.models import CourseBundle, Subject


class SubjectTranslationOptions(TranslationOptions):
    fields = ("subject",)
    required_languages = ("en", "de")


class CourseBundleTranslationOptions(TranslationOptions):
    fields = ("name",)
    required_languages = ("en", "de")


translator.register(Subject, SubjectTranslationOptions)
translator.register(CourseBundle, CourseBundleTranslationOptions)
