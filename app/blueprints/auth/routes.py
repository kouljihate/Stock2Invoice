from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.services.auth_service import AuthService
from app.models.user import UserModel

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    errors = AuthService.validate_registration(data)
    if errors:
        return jsonify({'errors': errors}), 422

    user_id = AuthService.register(data)
    return jsonify({'message': 'User registered successfully.', 'user_id': user_id}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 422

    user = AuthService.authenticate(email, password)
    if not user:
        return jsonify({'error': 'Invalid email or password.'}), 401

    token = create_access_token(
        identity=str(user['_id']),
        additional_claims={'role': user.get('role', 'user')}
    )
    return jsonify({
        'token': token,
        'user': UserModel.to_dict(user),
    }), 200


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    user = UserModel.find_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found.'}), 404
    return jsonify({'user': UserModel.to_dict(user)}), 200


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    update_data = {}
    if data.get('name'):
        update_data['name'] = data['name'].strip()
    if update_data:
        UserModel.update(user_id, update_data)
    user = UserModel.find_by_id(user_id)
    return jsonify({'user': UserModel.to_dict(user)}), 200
