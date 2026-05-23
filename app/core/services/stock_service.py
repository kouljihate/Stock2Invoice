import logging
import contextlib
from bson.objectid import ObjectId
from app.core.models.product_model import ProductModel
from app.core.models.stock_movement_model import StockMovementModel
from app.core.validators.common_validators import (
    validate_required,
    validate_string_length,
    validate_integer,
    validate_numeric,
    collect_errors,
)

logger = logging.getLogger(__name__)


class StockService:

    @staticmethod
    def validate(data, company_id, is_update=False):
        errors = []
        errors.append(validate_required(data.get('name'), 'Product name'))
        errors.append(validate_string_length(data.get('name'), 'Product name', 1, 200))
        errors.append(validate_required(data.get('sku'), 'SKU'))
        errors.append(validate_string_length(data.get('sku'), 'SKU', 1, 100))
        errors.append(validate_integer(data.get('quantity'), 'Quantity', 0))
        errors.append(validate_numeric(data.get('price'), 'Price', 0))
        if data.get('purchase_price') is not None:
            errors.append(validate_numeric(data.get('purchase_price'), 'Purchase price', 0))
        
        if data.get('quantity_min') is not None:
            errors.append(validate_integer(data.get('quantity_min'), 'Min quantity', 0))
        if not is_update:
            existing = ProductModel.find_by_sku(data.get('sku', '').strip(), company_id)
            if existing:
                errors.append('SKU already exists.')
        return collect_errors(errors)

    @staticmethod
    def create(data, user_id, company_id):
        clean = {
            'name': data['name'].strip(),
            'sku': data['sku'].strip(),
            'description': (data.get('description') or '').strip(),
            'quantity': int(data.get('quantity', 0)),
            'price': float(data.get('price', 0)),
            'purchase_price': float(data.get('purchase_price', 0)),
            'category': (data.get('category') or '').strip(),
            'subcategory': (data.get('subcategory') or '').strip(),
            'package_type': (data.get('package_type') or '').strip(),
            'brand': (data.get('brand') or '').strip(),
            'pack_size': float(data.get('pack_size', 0)),
            'pack_size_unit': (data.get('pack_size_unit') or '').strip(),
            'number_of_pack': int(data.get('number_of_pack', 0)),
            'quantity_min': int(data.get('quantity_min', 5)),
            'status': (data.get('status') or 'active').strip(),
            'company_id': ObjectId(company_id),
        }
        product_id = ProductModel.create(clean)
        logger.info('Product created: %s (sku=%s, id=%s, company=%s, by=%s)', clean['name'], clean['sku'], product_id, company_id, user_id)
        StockService._record_movement(product_id, clean['name'], clean['sku'], 'in',
                                      clean['quantity'], 0, clean['quantity'],
                                      'Initial stock', user_id, company_id)
        return product_id

    @staticmethod
    def get_by_id(product_id, company_id=None):
        product = ProductModel.find_by_id(product_id)
        if product and company_id and str(product.get('company_id', '')) != str(company_id):
            return None
        return product

    @staticmethod
    def get_by_sku(sku, company_id):
        return ProductModel.find_by_sku(sku, company_id)

    @staticmethod
    def list(page, per_page, filters=None, company_id=None):
        query = filters or {}
        if company_id:
            query['company_id'] = ObjectId(company_id)
        items, total = ProductModel.find_all(page, per_page, query)
        return [ProductModel.to_dict(item) for item in items], total

    @staticmethod
    def update(product_id, data, user_id, company_id):
        product = ProductModel.find_by_id(product_id)
        if not product:
            return None
        if str(product.get('company_id', '')) != company_id:
            return None
        old_qty = product.get('quantity', 0)
        clean = {}
        clean = {
            'name': data['name'].strip(),
            'sku': data['sku'].strip(),
            'description': (data.get('description') or '').strip(),
            'quantity': int(data.get('quantity', old_qty)),
            'price': float(data.get('price', product.get('price', 0))),
            'purchase_price': float(data.get('purchase_price', product.get('purchase_price', 0))),
            'category': (data.get('category') or '').strip(),
            'subcategory': (data.get('subcategory') or '').strip(),
            'package_type': (data.get('package_type') or '').strip(),
            'brand': (data.get('brand') or '').strip(),
            'pack_size': float(data.get('pack_size', product.get('pack_size', 0))),
            'pack_size_unit': (data.get('pack_size_unit') or '').strip(),
            'number_of_pack': int(data.get('number_of_pack', product.get('number_of_pack', 0))),
            'quantity_min': int(data.get('quantity_min', product.get('quantity_min', 5))),
            'status': (data.get('status') or 'active').strip(),
        }
        ProductModel.update(product_id, clean)
        new_qty = clean['quantity']
        diff = new_qty - old_qty
        if diff != 0:
            mv_type = 'in' if diff > 0 else 'out'
            StockService._record_movement(product_id, clean['name'], clean['sku'],
                                          mv_type, abs(diff), old_qty, new_qty,
                                          'Stock adjustment', user_id, company_id)
        logger.info('Product updated: %s (id=%s, by=%s)', clean['name'], product_id, user_id)
        return True

    @staticmethod
    def delete(product_id, user_id, company_id):
        product = ProductModel.find_by_id(product_id)
        if not product:
            return False
        if str(product.get('company_id', '')) != company_id:
            return False
        ProductModel.delete(product_id)
        logger.info('Product deleted: %s (id=%s, by=%s)', product.get('name'), product_id, user_id)
        return True

    @staticmethod
    def get_low_stock(company_id=None):
        filters = {}
        if company_id:
            filters['company_id'] = ObjectId(company_id)
        products = ProductModel.find_all_unpaginated(filters)
        return [ProductModel.to_dict(p) for p in products if p.get('quantity', 0) <= p.get('quantity_min', 5)]

    @staticmethod
    def get_category_summary(company_id=None):
        pipeline = [
            {'$match': {'company_id': ObjectId(company_id)}} if company_id else {'$match': {}},
            {'$group': {'_id': '$category', 'count': {'$sum': 1}, 'total_qty': {'$sum': '$quantity'},
                        'total_value': {'$sum': {'$multiply': ['$quantity', '$price']}}}},
            {'$sort': {'_id': 1}},
        ]
        if company_id:
            pipeline[0] = {'$match': {'company_id': ObjectId(company_id)}}
        if not company_id:
            pipeline = pipeline[1:]
        return ProductModel.aggregate(pipeline)

    @staticmethod
    def get_total_valuation(company_id=None):
        pipeline = []
        if company_id:
            pipeline.append({'$match': {'company_id': ObjectId(company_id)}})
        pipeline.append({'$group': {'_id': None, 'total_value': {'$sum': {'$multiply': ['$quantity', '$price']}},
                                    'total_products': {'$sum': 1}, 'total_qty': {'$sum': '$quantity'}}})
        result = ProductModel.aggregate(pipeline)
        return result[0] if result else {'total_value': 0, 'total_products': 0, 'total_qty': 0}

    @staticmethod
    def deduct_stock(sku, quantity, company_id, reference='', user_id=None):
        product = ProductModel.find_by_sku(sku, company_id)
        if not product:
            return False
        if product['quantity'] < quantity:
            return False
        new_qty = product['quantity'] - quantity
        ProductModel.update(str(product['_id']), {'quantity': new_qty})
        StockService._record_movement(str(product['_id']), product['name'], sku, 'out',
                                      quantity, product['quantity'], new_qty,
                                      reference or 'Invoice deduction', user_id, company_id)
        return True

    @staticmethod
    def get_movements(page, per_page, product_id=None, company_id=None):
        filters = {}
        if company_id:
            filters['company_id'] = ObjectId(company_id)
        if product_id:
            filters['product_id'] = ObjectId(product_id)
        items, total = StockMovementModel.find_all(page, per_page, filters)
        return [StockMovementModel.to_dict(item) for item in items], total

    @staticmethod
    def get_recent_movements(limit=10, company_id=None):
        filters = {}
        if company_id:
            filters['company_id'] = ObjectId(company_id)
        items = StockMovementModel.recent(limit, filters)
        return [StockMovementModel.to_dict(item) for item in items]

    @staticmethod
    def _record_movement(product_id, product_name, sku, mv_type, quantity, qty_before, qty_after, reason, user_id, company_id):
        from app.core.services.event_service import EventService
        with contextlib.suppress(Exception):
            EventService.record(company_id, 'product', product_id, sku, 'stock_movement',
                                changes={'quantity': quantity, 'reason': reason,
                                         'quantity_before': qty_before, 'quantity_after': qty_after,
                                         'type': mv_type},
                                user_id=user_id, user_name='')
