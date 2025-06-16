from django import template

register = template.Library()

@register.filter
def get_role(rates, role_name):
    return rates.filter(role=role_name)
