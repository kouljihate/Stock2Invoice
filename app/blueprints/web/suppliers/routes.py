import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.core.models.user_model import UserModel
from app.core.models.supplier_model import SupplierModel
from app.core.utils.helpers import paginate

logger = logging.getLogger(__name__)
web_suppliers_bp = Blueprint('web_suppliers', __name__, template_folder='../../../templates')


def _get_user():
    uid = get_jwt_identity()
    return UserModel.find_by_id(uid)


def _company_id():
    claims = get_jwt()
    return claims.get('company_id')


@web_suppliers_bp.route('')
@web_suppliers_bp.route('/')
@jwt_required()
def list_suppliers():
    try:
        page, per_page = paginate(request.args.get('page', 1), request.args.get('per_page', 20))
        cid = _company_id()
        from bson.objectid import ObjectId
        filters = {'company_id': ObjectId(cid)} if cid else {}
        items, total = SupplierModel.find_all(page, per_page, filters)
        user = _get_user()
        return render_template('suppliers/list.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               suppliers=[SupplierModel.to_dict(s) for s in items],
                               total=total, page=page, per_page=per_page,
                               pages=(total + per_page - 1) // per_page)
    except Exception:
        logger.exception('Supplier list error')
        return render_template('suppliers/list.html', mode='web', suppliers=[], total=0, page=1, per_page=20, pages=0)


@web_suppliers_bp.route('/create', methods=['GET', 'POST'])
@jwt_required()
def create_supplier():
    user = _get_user()
    if request.method == 'GET':
        return render_template('suppliers/form.html', mode='web',
                               user=UserModel.to_dict(user) if user else None, supplier=None)
    try:
        cid = _company_id()
        from bson.objectid import ObjectId
        data = {
            'name': request.form.get('name', '').strip(),
            'contact_name': request.form.get('contact_name', '').strip(),
            'email': request.form.get('email', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'address': request.form.get('address', '').strip(),
            'city': request.form.get('city', '').strip(),
            'ice': request.form.get('ice', '').strip(),
            'rc': request.form.get('rc', '').strip(),
            'payment_terms': request.form.get('payment_terms', '').strip(),
            'company_id': ObjectId(cid),
        }
        if not data['name']:
            flash('Supplier name is required.', 'danger')
            return render_template('suppliers/form.html', mode='web',
                                   user=UserModel.to_dict(user) if user else None, supplier=request.form)
        SupplierModel.create(data)
        flash('Supplier created.', 'success')
        return redirect(url_for('web_suppliers.list_suppliers'))
    except Exception as e:
        logger.exception('Supplier create error')
        flash(f'Could not create supplier: {e}', 'danger')
        return render_template('suppliers/form.html', mode='web',
                               user=UserModel.to_dict(user) if user else None, supplier=request.form)


@web_suppliers_bp.route('/<supplier_id>/edit', methods=['GET', 'POST'])
@jwt_required()
def edit_supplier(supplier_id):
    user = _get_user()
    supplier = SupplierModel.find_by_id(supplier_id)
    if not supplier:
        flash('Supplier not found.', 'danger')
        return redirect(url_for('web_suppliers.list_suppliers'))
    if request.method == 'GET':
        return render_template('suppliers/form.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               supplier=SupplierModel.to_dict(supplier))
    try:
        data = {k: request.form.get(k, '').strip() for k in ('name', 'contact_name', 'email', 'phone', 'address', 'city', 'ice', 'rc', 'payment_terms')}
        if not data['name']:
            flash('Supplier name is required.', 'danger')
            return render_template('suppliers/form.html', mode='web',
                                   user=UserModel.to_dict(user) if user else None, supplier=request.form)
        SupplierModel.update(supplier_id, data)
        flash('Supplier updated.', 'success')
        return redirect(url_for('web_suppliers.list_suppliers'))
    except Exception as e:
        logger.exception('Supplier edit error')
        flash(f'Could not update supplier: {e}', 'danger')
        return render_template('suppliers/form.html', mode='web',
                               user=UserModel.to_dict(user) if user else None, supplier=request.form)


@web_suppliers_bp.route('/<supplier_id>/delete', methods=['POST'])
@jwt_required()
def delete_supplier(supplier_id):
    supplier = SupplierModel.find_by_id(supplier_id)
    if not supplier:
        flash('Supplier not found.', 'danger')
    else:
        SupplierModel.delete(supplier_id)
        flash('Supplier deleted.', 'success')
    return redirect(url_for('web_suppliers.list_suppliers'))