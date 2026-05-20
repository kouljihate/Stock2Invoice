import re


def validate_required(value, field_name):
    if not value or not str(value).strip():
        return f'{field_name} is required.'
    return None


def validate_string_length(value, field_name, min_len=1, max_len=255):
    v = (value or '').strip()
    if len(v) < min_len:
        return f'{field_name} must be at least {min_len} characters.'
    if len(v) > max_len:
        return f'{field_name} must not exceed {max_len} characters.'
    return None


def validate_email_format(value):
    import email_validator
    try:
        email_validator.validate_email(value)
        return None
    except email_validator.EmailNotValidError:
        return 'Invalid email address.'


def validate_password_strength(value):
    errors = []
    if len(value) < 8:
        errors.append('Password must be at least 8 characters.')
    if not re.search(r'[A-Za-z]', value):
        errors.append('Password must contain at least one letter.')
    if not re.search(r'\d', value):
        errors.append('Password must contain at least one digit.')
    return errors


def validate_numeric(value, field_name, min_val=0, max_val=None):
    try:
        v = float(value)
        if v < min_val:
            return f'{field_name} cannot be less than {min_val}.'
        if max_val is not None and v > max_val:
            return f'{field_name} cannot exceed {max_val}.'
        return None
    except (ValueError, TypeError):
        return f'{field_name} must be a valid number.'


def validate_integer(value, field_name, min_val=0, max_val=None):
    try:
        v = int(value)
        if v < min_val:
            return f'{field_name} cannot be less than {min_val}.'
        if max_val is not None and v > max_val:
            return f'{field_name} cannot exceed {max_val}.'
        return None
    except (ValueError, TypeError):
        return f'{field_name} must be a valid integer.'


def validate_choice(value, choices, field_name):
    if value not in choices:
        return f'{field_name} must be one of: {", ".join(choices)}.'
    return None


def collect_errors(validators):
    return [e for e in validators if e is not None]
