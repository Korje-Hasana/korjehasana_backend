from django import template

register = template.Library()

BENGALI_DIGITS = {
    '0': '০',
    '1': '১',
    '2': '২',
    '3': '৩',
    '4': '৪',
    '5': '৫',
    '6': '৬',
    '7': '৭',
    '8': '৮',
    '9': '৯',
}

def to_bengali_digits(s):
    return ''.join(BENGALI_DIGITS.get(ch, ch) for ch in s)

@register.filter
def bdtaka(value):
    try:
        value = int(value)
    except (ValueError, TypeError):
        return value

    # Indian comma formatting
    s = str(value)
    if len(s) <= 3:
        formatted = s
    else:
        formatted = s[-3:]
        s = s[:-3]
        while len(s) > 2:
            formatted = s[-2:] + ',' + formatted
            s = s[:-2]
        if s:
            formatted = s + ',' + formatted

    # Convert to Bengali digits and add Taka sign
    return f"৳ {to_bengali_digits(formatted)}"
