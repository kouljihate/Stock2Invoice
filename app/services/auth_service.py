import re
from email_validator import validate_email, EmailNotValidError
from app.extensions import bcrypt
from app.models.user import UserModel


class AuthService:

    @staticmethod
    def validate_registration(data):
        errors = []

        name = (data.get('name') or '').strip()
        if not name or len(name) < 2:
            errors.append('Name must be at least 2 characters.')

        email = (data.get('email') or '').strip().lower()
        try:
            validate_email(email)
        except EmailNotValidError:
            errors.append('Invalid email address.')

        password = data.get('password', '')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
            errors.append('Password must contain both letters and numbers.')

        existing = UserModel.find_by_email(email)
        if existing:
            errors.append('Email already registered.')

        return errors

    @staticmethod
    def register(data):
        hashed = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        user_data = {
            'name': data['name'].strip(),
            'email': data['email'].strip().lower(),
            'password': hashed,
            'role': 'user',
        }
        user_id = UserModel.create(user_data)
        return user_id

    @staticmethod
    def authenticate(email, password):
        user = UserModel.find_by_email(email.strip().lower())
        if not user:
            return None
        if not bcrypt.check_password_hash(user['password'], password):
            return None
        return user
