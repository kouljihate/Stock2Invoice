from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services.stock_service import StockService
from app.utils.helpers import paginate

stock_bp = Blueprint('stock', __name__)


@stock_bp.route('', methods=['GET'])
@jwt_required()
def list_stock():
    page, per_page = paginate(
        request.args.get('page', 1),
        request.args.get('per_page', 20),
    )
    filters = {}
    if request.args.get('category'):
        filters['category'] = request.args['category']
    if request.args.get('search'):
        import re
        regex = {'$regex': re.escape(request.args['search']), '$options': 'i'}
        filters['$or'] = [
            {'name': regex},
            {'sku': regex},
            {'description': regex},
        ]
    items, total = StockService.list(page, per_page, filters)
    return jsonify({
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page,
    }), 200


@stock_bp.route('', methods=['POST'])
@jwt_required()
def create_stock():
    data = request.get_json(silent=True) or {}
    errors, clean = StockService.validate(data)
    if errors:
        return jsonify({'errors': errors}), 422
    stock_id = StockService.create(clean)
    return jsonify({'message': 'Stock item created.', 'id': stock_id}), 201


@stock_bp.route('/<stock_id>', methods=['GET'])
@jwt_required()
def get_stock(stock_id):
    item = StockService.get_by_id(stock_id)
    if not item:
        return jsonify({'error': 'Stock item not found.'}), 404
    return jsonify({'item': StockService.to_dict(item)}), 200


@stock_bp.route('/<stock_id>', methods=['PUT'])
@jwt_required()
def update_stock(stock_id):
    item = StockService.get_by_id(stock_id)
    if not item:
        return jsonify({'error': 'Stock item not found.'}), 404

    data = request.get_json(silent=True) or {}
    errors, clean = StockService.validate(data)
    if errors:
        return jsonify({'errors': errors}), 422

    StockService.update(stock_id, clean)
    return jsonify({'message': 'Stock item updated.'}), 200


@stock_bp.route('/<stock_id>', methods=['DELETE'])
@jwt_required()
def delete_stock(stock_id):
    item = StockService.get_by_id(stock_id)
    if not item:
        return jsonify({'error': 'Stock item not found.'}), 404
    StockService.delete(stock_id)
    return jsonify({'message': 'Stock item deleted.'}), 200
