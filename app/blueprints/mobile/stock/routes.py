import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.core.services.stock_service import StockService
from app.core.models.user_model import UserModel
from app.core.utils.helpers import paginate

logger = logging.getLogger(__name__)
mobile_stock_bp = Blueprint('mobile_stock', __name__, template_folder='../../../templates')


def _get_user():
    uid = get_jwt_identity()
    return UserModel.find_by_id(uid)


def _company_id():
    claims = get_jwt()
    return claims.get('company_id')


@mobile_stock_bp.route('')
@mobile_stock_bp.route('/')
@jwt_required()
def list_products():
    try:
        page, per_page = paginate(request.args.get('page', 1), 20)
        filters = {}
        if request.args.get('search'):
            import re
            regex = {'$regex': re.escape(request.args['search']), '$options': 'i'}
            filters['$or'] = [{'name': regex}, {'sku': regex}]
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
    if request.method == 'GET':
        return render_template('stock/edit.html', mode='mobile',
                               user=UserModel.to_dict(user) if user else None, product=None)
    try:
        cid = _company_id()
        errors = StockService.validate(request.form.to_dict(), cid)
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('stock/edit.html', mode='mobile',
                                   user=UserModel.to_dict(user) if user else None, product=request.form)
        user_id = get_jwt_identity()
        StockService.create(request.form.to_dict(), user_id, cid)
        flash('Product created.', 'success')
        return redirect(url_for('mobile_stock.list_products'))
    except Exception as e:
        logger.exception('Mobile product create error')
        flash('Could not create product.', 'danger')
        return render_template('stock/edit.html', mode='mobile',
                               user=UserModel.to_dict(user) if user else None, product=request.form)


@mobile_stock_bp.route('/<product_id>/edit', methods=['GET', 'POST'])
@jwt_required()
def edit_product(product_id):
    user = _get_user()
    cid = _company_id()
    product = StockService.get_by_id(product_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('mobile_stock.list_products'))
    if request.method == 'GET':
        return render_template('stock/edit.html', mode='mobile',
                               user=UserModel.to_dict(user) if user else None, product=product)
    try:
        data = request.form.to_dict()
        data['sku'] = product['sku']
        errors = StockService.validate(data, cid, is_update=True)
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('stock/edit.html', mode='mobile',
                                   user=UserModel.to_dict(user) if user else None, product=data)
        user_id = get_jwt_identity()
        StockService.update(product_id, data, user_id, cid)
        flash('Product updated.', 'success')
        return redirect(url_for('mobile_stock.list_products'))
    except Exception as e:
        logger.exception('Mobile product update error')
        flash('Could not update product.', 'danger')
        return render_template('stock/edit.html', mode='mobile',
                               user=UserModel.to_dict(user) if user else None, product=request.form)


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
    product = StockService.get_by_id(product_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('mobile_stock.list_products'))
    movements, total = StockService.get_movements(1, 20, product_id, cid)
    return render_template('stock/detail.html', mode='mobile',
                           user=UserModel.to_dict(user) if user else None,
                           product=product, movements=movements, total=total, page=1, per_page=20,
                           pages=(total + 19) // 20)
