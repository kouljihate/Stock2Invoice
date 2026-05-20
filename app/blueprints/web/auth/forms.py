from app.core.validators.common_validators import validate_required, validate_email_format, validate_string_length, validate_password_strength


class LoginForm:
    def __init__(self, data):
        self.data = data or {}
        self.errors = []

    def validate(self):
        email = (self.data.get('email') or '').strip()
        password = self.data.get('password', '')
        self.errors.append(validate_required(email, 'Email'))
        self.errors.append(validate_email_format(email))
        self.errors.append(validate_required(password, 'Password'))
        self.errors = [e for e in self.errors if e]
        return len(self.errors) == 0

    @property
    def email(self):
        return (self.data.get('email') or '').strip().lower()

    @property
    def password(self):
        return self.data.get('password', '')


class RegisterForm:
    def __init__(self, data):
        self.data = data or {}
        self.errors = []

    def validate(self):
        name = (self.data.get('name') or '').strip()
        email = (self.data.get('email') or '').strip().lower()
        password = self.data.get('password', '')
        confirm = self.data.get('confirm_password', '')

        self.errors.append(validate_required(name, 'Name'))
        self.errors.append(validate_string_length(name, 'Name', 2, 100))
        self.errors.append(validate_required(email, 'Email'))
        self.errors.append(validate_email_format(email))
        self.errors.append(validate_required(password, 'Password'))
        self.errors.extend(validate_password_strength(password))
        if password != confirm:
            self.errors.append('Passwords do not match.')
        self.errors = [e for e in self.errors if e]
        return len(self.errors) == 0

    @property
    def name(self):
        return (self.data.get('name') or '').strip()

    @property
    def email(self):
        return (self.data.get('email') or '').strip().lower()

    @property
    def password(self):
        return self.data.get('password', '')
