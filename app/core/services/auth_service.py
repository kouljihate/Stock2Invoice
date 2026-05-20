import logging
from app.extensions.db import bcrypt
from app.core.models.user_model import UserModel
from app.core.validators.common_validators import (
    validate_required,
    validate_email_format,
    validate_string_length,
    validate_password_strength,
    collect_errors,
)

logger = logging.getLogger(__name__)


class AuthService:

    @staticmethod
    def validate_registration(data, company_id=None):
        errors = []
        errors.append(validate_required(data.get('name'), 'Name'))
        errors.append(validate_string_length(data.get('name'), 'Name', 2, 100))
        email = (data.get('email') or '').strip().lower()
        errors.append(validate_required(email, 'Email'))
        errors.append(validate_email_format(email))
        pw = data.get('password', '')
        errors.append(validate_required(pw, 'Password'))
        errors.extend(validate_password_strength(pw))
        existing = UserModel.find_by_email(email, company_id)
        if existing:
            errors.append('Email already registered.')
        return collect_errors(errors), email

    @staticmethod
    def register(data, company_id=None):
        hashed = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        user_data = {
            'name': data['name'].strip(),
            'email': data['email'].strip().lower(),
            'password': hashed,
            'role': data.get('role', 'user'),
        }
        if company_id:
            from bson.objectid import ObjectId
            user_data['company_id'] = ObjectId(company_id)
        user_id = UserModel.create(user_data)
        logger.info('User registered: %s (id=%s, company=%s)', user_data['email'], user_id, company_id)
        return user_id

    @staticmethod
    def authenticate(email, password):
        user = UserModel.find_by_email(email.strip().lower())
        if not user:
            logger.warning('Login failed — unknown email: %s', email)
            return None
        if not bcrypt.check_password_hash(user['password'], password):
            logger.warning('Login failed — wrong password: %s', email)
            return None
        logger.info('Login success: %s (role=%s, company=%s)', email, user.get('role'), user.get('company_id'))
        return user
