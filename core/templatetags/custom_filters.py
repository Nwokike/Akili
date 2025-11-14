from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Allows dictionary lookup using a variable key in Django templates."""
    try:
        # Convert key to string if it's an integer, as JSONField keys are usually strings
        if isinstance(key, int):
            key = str(key)
        return dictionary.get(key)
    except AttributeError:
        return None