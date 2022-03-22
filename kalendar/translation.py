from modeltranslation.translator import TranslationOptions, translator

from kalendar.models import Location


class LocationTranslationOptions(TranslationOptions):
    fields = ("shortname", "address")
    required_languages = ("en", "de")


translator.register(Location, LocationTranslationOptions)
