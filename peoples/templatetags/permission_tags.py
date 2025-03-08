from django import template

register = template.Library()

@register.simple_tag
def has_group(user, *group_names):
    """Check if a user belongs to any of the given groups"""
    return user.groups.filter(name__in=group_names).exists()