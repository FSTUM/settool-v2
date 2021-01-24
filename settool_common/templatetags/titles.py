import random

from django import template

register = template.Library()


@register.simple_tag
def random_title():
    titles = [
        "SET's roll",
        "SET's Rock'n Roll",
        "Never SET Me Down",
        "I Won't SET You Down",
        "SET's Go Crazy",
        "SET It Rock",
        "The trendSETters",
        "Enjoy the sunSET",
        "Lets SETle this",
        "SET me if you can",
        "Das UmSETz Referat",
        "Die besten ReiSETipps beim SET-Referat",
        "May the SET be ever in your favor",
        "S.E.T. - SEe The awesomeness",
        "S.E.T. - SEe The excellence",
    ]
    return random.choice(titles)  # nosec: fully defined
