import os

from django import template

from settool.settings import BASE_DIR

register = template.Library()


@register.filter
def latex_escape(string):
    string = str(string)

    string = string.replace("\\", "\\textbackslash")
    string = string.replace(" ", "\\ ")
    string = string.replace(
        "\\textbackslash",
        "\\textbackslash ",
    )  # needed to break out of circular dependency between the first two replacements
    string = string.replace("&", "\\&")
    string = string.replace("%", "\\%")
    string = string.replace("$", "\\$")
    string = string.replace("#", "\\#")
    string = string.replace("_", "\\_")
    string = string.replace("{", "\\{")
    string = string.replace("}", "\\}")
    string = string.replace("~", "\\textasciitilde ")
    string = string.replace("^", "\\textasciicircum ")

    return f"{{{string}}}"


@register.simple_tag
def fslogo_path():
    return f'{{{os.path.join(BASE_DIR, "static", "eule.png")}}}'
