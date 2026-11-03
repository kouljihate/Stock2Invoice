import logging
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.core.services.stock_service import StockService
from app.core.models.user_model import UserModel
from app.core.models.supplier_model import SupplierModel
from app.core.utils.helpers import paginate
from bson.objectid import ObjectId

logger = logging.getLogger(__name__)
mobile_stock_bp = Blueprint('mobile_stock', __name__, template_folder='../../../templates')


def _get_user():
    """Acting user document, resolved from the database (never claims)."""
    from app.core.utils.context import current_user
    return current_user()


def _company_id():
    """Acting user's company id, resolved from the database (never claims)."""
    from app.core.utils.context import current_company_id
    return current_company_id()


@mobile_stock_bp.route('')
@mobile_stock_bp.route('/')
@jwt_required()
def list_products():
    try:
        page, per_page = paginate(request.args.get('page', 1), 20)
        filters = {}
        if request.args.get('search'):
            regex = {'$regex': re.escape(request.args['search']), '$options': 'i'}
            filters['$or'] = [{'name': regex}, {'sku': regex}]
        if request.args.get('brand'):
            filters['brand'] = {'$regex': re.escape(request.args['brand']), '$options': 'i'}
        cid = _company_id()
        items, total = StockService.list(page, per_page, filters, cid)
        user = _get_user()
        return render_template('stock/list.html', mode='mobile',
                               user=UserModel.to_dict(user) if user else None,
                               products=items, total=total, page=page, per_page=per_page,
                               pages=(total + per_page - 1) // per_page)
    except Exception as e:
        logger.exception('Mobile stock list error')
        flash('Could not load products.', 'danger')
        return render_template('stock/list.html', mode='mobile',
                               products=[], total=0, page=1, per_page=20, pages=0)


@mobile_stock_bp.route('/create', methods=['GET', 'POST'])
@jwt_required()
def create_product():
    user = _get_user()
    cid = _company_id()
    suppliers = []
    if cid:
        suppliers = [SupplierModel.to_dict(s) for s in SupplierModel.find_all_unpaginated({'company_id': ObjectId(cid)})]
    if request.method == 'GET':
        return render_template('stock/edit.html', mode='mobile',
                               user=UserModel.to_dict(user) if user else None, product=None, suppliers=suppliers)
    try:
        cid = _company_id()
        data = request.form.to_dict()
        if data.get('supplier_id'):
            sup = SupplierModel.find_by_id(data['supplier_id'])
            data['supplier_name'] = sup.get('name', '') if sup else ''
        errors = StockService.validate(data, cid)
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('stock/edit.html', mode='mobile',
                                   user=UserModel.to_dict(user) if user else None, product=data, suppliers=suppliers)
        user_id = get_jwt_identity()
        StockService.create(data, user_id, cid)
        flash('Product created.', 'success')
        return redirect(url_for('mobile_stock.list_products'))
    except Exception as e:
        logger.exception('Mobile product create error')
        flash('Could not create product.', 'danger')
        return render_template('stock/edit.html', mode='mobile',
                               user=UserModel.to_dict(user) if user else None, product=request.form, suppliers=suppliers)


@mobile_stock_bp.route('/<product_id>/edit', methods=['GET', 'POST'])
@jwt_required()
def edit_product(product_id):
    user = _get_user()
    cid = _company_id()
    product = StockService.get_by_id(product_id, cid)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('mobile_stock.list_products'))
    suppliers = []
    if cid:
        suppliers = [SupplierModel.to_dict(s) for s in SupplierModel.find_all_unpaginated({'company_id': ObjectId(cid)})]
    if request.method == 'GET':
        return render_template('stock/edit.html', mode='mobile',
                               user=UserModel.to_dict(user) if user else None, product=product, suppliers=suppliers)
    try:
        data = request.form.to_dict()
        data['sku'] = product['sku']
        if data.get('supplier_id'):
            sup = SupplierModel.find_by_id(data['supplier_id'])
            data['supplier_name'] = sup.get('name', '') if sup else ''
        errors = StockService.validate(data, cid, is_update=True)
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('stock/edit.html', mode='mobile',
                                   user=UserModel.to_dict(user) if user else None, product=data, suppliers=suppliers)
        user_id = get_jwt_identity()
        StockService.update(product_id, data, user_id, cid)
        flash('Product updated.', 'success')
        return redirect(url_for('mobile_stock.list_products'))
    except Exception as e:
        logger.exception('Mobile product update error')
        flash('Could not update product.', 'danger')
        return render_template('stock/edit.html', mode='mobile',
                               user=UserModel.to_dict(user) if user else None, product=request.form, suppliers=suppliers)


@mobile_stock_bp.route('/<product_id>/delete', methods=['POST'])
@jwt_required()
def delete_product(product_id):
    try:
        user_id = get_jwt_identity()
        cid = _company_id()
        StockService.delete(product_id, user_id, cid)
        flash('Product deleted.', 'success')
    except Exception as e:
        logger.exception('Mobile product delete error')
        flash('Could not delete product.', 'danger')
    return redirect(url_for('mobile_stock.list_products'))


@mobile_stock_bp.route('/<product_id>')
@jwt_required()
def view_product(product_id):
    user = _get_user()
    cid = _company_id()
    product = StockService.get_by_id(product_id, cid)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('mobile_stock.list_products'))
    movements, total = StockService.get_movements(1, 20, product_id, cid)
    return render_template('stock/detail.html', mode='mobile',
                           user=UserModel.to_dict(user) if user else None,
                           product=product, movements=movements, total=total, page=1, per_page=20,
                           pages=(total + 19) // 20)
