import logging
from datetime import datetime, timezone
from bson.objectid import ObjectId
from app.core.models.order_model import OrderModel
from app.core.models.invoice_model import InvoiceModel
from app.core.models.product_model import ProductModel
from app.core.services.stock_service import StockService
from app.core.validators.common_validators import (
    validate_required,
    validate_numeric,
    collect_errors,
)

logger = logging.getLogger(__name__)


class OrderService:

    @staticmethod
    def validate(data, company_id):
        errors = []
        errors.append(validate_required(data.get('customer_name'), 'Customer name'))

        items = data.get('items', [])
        if not items or not isinstance(items, list):
            errors.append('At least one line item is required.')
            return collect_errors(errors)

        for idx, item in enumerate(items):
            sku = item.get('sku', '').strip()
            if not sku:
                errors.append(f'Item {idx + 1}: SKU is required.')
                continue
            product = ProductModel.find_by_sku(sku, company_id)
            if not product:
                errors.append(f'Item {idx + 1}: Product with SKU "{sku}" not found.')
                continue
            qty = item.get('quantity', 0)
            try:
                qty = int(qty)
                if qty <= 0:
                    errors.append(f'Item {idx + 1}: Quantity must be positive.')
            except (ValueError, TypeError):
                errors.append(f'Item {idx + 1}: Quantity must be an integer.')

        if data.get('discount_percent'):
            err = validate_numeric(data.get('discount_percent'), 'Discount', 0, 100)
            if err:
                errors.append(err)

        return collect_errors(errors)

    @staticmethod
    def create(data, user_id, company_id):
        items = []
        subtotal = 0.0
        for it in data['items']:
            product = ProductModel.find_by_sku(it['sku'], company_id)
            qty = int(it['quantity'])
            up = float(it.get('unit_price', product['price']))
            line_total = round(qty * up, 2)
            items.append({
                'sku': it['sku'],
                'name': it.get('name', product['name']),
                'description': it.get('description', product.get('description', '')),
                'quantity': qty,
                'unit_price': up,
                'total': line_total,
            })
            subtotal += line_total

        discount_pct = float(data.get('discount_percent', 0))
        discount_amt = round(subtotal * (discount_pct / 100), 2)
        after_discount = subtotal - discount_amt

        tax_percent = float(data.get('tax_percent', 10))
        tax_amount = round(after_discount * (tax_percent / 100), 2)
        total = round(after_discount + tax_amount, 2)

        now = datetime.now(timezone.utc)
        count = OrderModel.count({'company_id': ObjectId(company_id)})

        order_data = {
            'order_number': f"O{datetime.now().strftime('%d%m%y')}-{count + 1:02d}",
            'customer_name': data['customer_name'].strip(),
            'contact_name': (data.get('contact_name') or '').strip(),
            'contact_email': (data.get('contact_email') or '').strip(),
            'customer_address': (data.get('customer_address') or '').strip(),
            'items': items,
            'subtotal': round(subtotal, 2),
            'discount_percent': discount_pct,
            'discount_amount': discount_amt,
            'tax_percent': tax_percent,
            'tax_amount': tax_amount,
            'total': total,
            'status': data.get('status', 'pending'),
            'notes': (data.get('notes') or '').strip(),
            'company_id': ObjectId(company_id),
            'created_by': ObjectId(user_id) if isinstance(user_id, str) else user_id,
            'generated_invoice_id': None,
            'generated_invoice_number': None,
        }

        order_id = OrderModel.create(order_data)
        logger.info('Order created: %s (id=%s, company=%s, total=%.2f, by=%s)',
                     order_data['order_number'], order_id, company_id, total, user_id)

        if order_data['status'] == 'confirmed':
            OrderService._generate_invoice(order_id, order_data, user_id, company_id)

        return order_id, order_data['order_number']

    @staticmethod
    def update(order_id, data, user_id, company_id):
        order = OrderModel.find_by_id(order_id)
        if not order:
            return None
        if str(order.get('company_id', '')) != company_id:
            return None

        old_status = order.get('status')
        new_status = data.get('status', old_status)
        update_data = {'status': new_status}

        if data.get('notes'):
            update_data['notes'] = data['notes'].strip()
        if data.get('customer_name'):
            update_data['customer_name'] = data['customer_name'].strip()
        if 'contact_name' in data:
            update_data['contact_name'] = data['contact_name'].strip()
        if 'contact_email' in data:
            update_data['contact_email'] = data['contact_email'].strip()

        OrderModel.update(order_id, update_data)
        logger.info('Order updated: %s (id=%s, status=%s->%s, by=%s)',
                     order.get('order_number'), order_id, old_status, new_status, user_id)

        if new_status == 'confirmed' and old_status != 'confirmed' and not order.get('generated_invoice_id'):
            OrderService._generate_invoice(order_id, {**order, **update_data}, user_id, company_id)

        return True

    @staticmethod
    def _generate_invoice(order_id, order_data, user_id, company_id):
        try:
            invoice_data = {
                'customer_name': order_data['customer_name'],
                'contact_name': order_data.get('contact_name', ''),
                'contact_email': order_data.get('contact_email', ''),
                'customer_address': order_data.get('customer_address', ''),
                'items': order_data['items'],
                'discount_percent': order_data.get('discount_percent', 0),
                'tax_percent': order_data.get('tax_percent', 10),
                'status': 'sent',
                'notes': f'Auto-generated from Order {order_data.get("order_number")}',
            }

            inv_count = InvoiceModel.count({'company_id': ObjectId(company_id)})
            invoice_number = f"I{datetime.now().strftime('%d%m%y')}-{inv_count + 1:02d}"
            now = datetime.now(timezone.utc)
            doc = {
                'invoice_number': invoice_number,
                'customer_name': invoice_data['customer_name'],
                'contact_name': invoice_data.get('contact_name', ''),
                'contact_email': invoice_data.get('contact_email', ''),
                'customer_address': invoice_data.get('customer_address', ''),
                'invoice_date': now,
                'due_date': now,
                'items': invoice_data['items'],
                'subtotal': float(order_data.get('subtotal', 0)),
                'discount_percent': float(invoice_data['discount_percent']),
                'discount_amount': float(order_data.get('discount_amount', 0)),
                'tax_percent': float(invoice_data['tax_percent']),
                'tax_amount': float(order_data.get('tax_amount', 0)),
                'total': float(order_data.get('total', 0)),
                'status': 'sent',
                'notes': invoice_data['notes'],
                'company_id': ObjectId(company_id),
                'created_by': ObjectId(user_id) if isinstance(user_id, str) else user_id,
                'from_order_id': ObjectId(order_id) if isinstance(order_id, str) else order_id,
                'from_order_number': order_data.get('order_number'),
            }
            invoice_id = InvoiceModel.create(doc)

            OrderModel.update(order_id, {
                'generated_invoice_id': ObjectId(invoice_id),
                'generated_invoice_number': invoice_number,
            })

            for it in order_data['items']:
                StockService.deduct_stock(it['sku'], it['quantity'], company_id,
                                          reference=f'Order {order_data.get("order_number")} → Invoice {invoice_number}',
                                          user_id=user_id)

            logger.info('Invoice %s auto-generated from Order %s', invoice_number, order_data.get('order_number'))
        except Exception as e:
            logger.exception('Failed to generate invoice from order %s', order_id)

    @staticmethod
    def get_by_id(order_id):
        order = OrderModel.find_by_id(order_id)
        return OrderModel.to_dict(order) if order else None

    @staticmethod
    def list(page, per_page, filters=None, company_id=None):
        query = filters or {}
        if company_id:
            query['company_id'] = ObjectId(company_id)
        items, total = OrderModel.find_all(page, per_page, query)
        return [OrderModel.to_dict(item) for item in items], total

    @staticmethod
    def get_recent(limit=5, company_id=None):
        filters = {}
        if company_id:
            filters['company_id'] = ObjectId(company_id)
        items = OrderModel.recent(limit, filters)
        return [OrderModel.to_dict(item) for item in items]

    @staticmethod
    def get_counts(company_id=None):
        filters = {}
        if company_id:
            filters['company_id'] = ObjectId(company_id)
        total = OrderModel.count(filters)
        return {
            'total': total,
            'pending': OrderModel.count({**filters, 'status': 'pending'}),
            'confirmed': OrderModel.count({**filters, 'status': 'confirmed'}),
            'shipped': OrderModel.count({**filters, 'status': 'shipped'}),
            'delivered': OrderModel.count({**filters, 'status': 'delivered'}),
            'cancelled': OrderModel.count({**filters, 'status': 'cancelled'}),
        }


