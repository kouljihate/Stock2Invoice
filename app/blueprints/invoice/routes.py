from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.invoice_service import InvoiceService
from app.utils.helpers import paginate

invoice_bp = Blueprint('invoice', __name__)


@invoice_bp.route('', methods=['GET'])
@jwt_required()
def list_invoices():
    page, per_page = paginate(
        request.args.get('page', 1),
        request.args.get('per_page', 20),
    )
    filters = {}
    if request.args.get('status'):
        filters['status'] = request.args['status']
    items, total = InvoiceService.list(page, per_page, filters)
    return jsonify({
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page,
    }), 200


@invoice_bp.route('', methods=['POST'])
@jwt_required()
def create_invoice():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    errors, clean = InvoiceService.validate(data)
    if errors:
        return jsonify({'errors': errors}), 422

    invoice_id, invoice_number = InvoiceService.create(data, user_id)
    return jsonify({
        'message': 'Invoice created.',
        'id': invoice_id,
        'invoice_number': invoice_number,
    }), 201


@invoice_bp.route('/<invoice_id>', methods=['GET'])
@jwt_required()
def get_invoice(invoice_id):
    inv = InvoiceService.get_by_id(invoice_id)
    if not inv:
        return jsonify({'error': 'Invoice not found.'}), 404
    return jsonify({'invoice': inv}), 200


@invoice_bp.route('/<invoice_id>/pdf', methods=['GET'])
@jwt_required()
def download_pdf(invoice_id):
    pdf = InvoiceService.generate_pdf(invoice_id)
    if not pdf:
        return jsonify({'error': 'Invoice not found.'}), 404
    return send_file(
        pdf,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'invoice-{invoice_id}.pdf',
    )
