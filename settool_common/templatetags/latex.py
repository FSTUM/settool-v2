from django import template

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
