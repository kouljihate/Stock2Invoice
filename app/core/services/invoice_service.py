import logging
from datetime import datetime, timezone, timedelta
from bson.objectid import ObjectId
from app.core.models.invoice_model import InvoiceModel
from app.extensions.db import mongo
from app.core.models.product_model import ProductModel
from app.core.services.stock_service import StockService
from app.core.validators.common_validators import (
    validate_required,
    validate_numeric,
    collect_errors,
)

logger = logging.getLogger(__name__)


class InvoiceService:

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
                elif product['quantity'] < qty and data.get('status') == 'paid':
                    errors.append(f'Item {idx + 1}: Insufficient stock for "{sku}" (available: {product["quantity"]}).')
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

        count = InvoiceModel.count({'company_id': ObjectId(company_id)})
        invoice_number = f"I{datetime.now().strftime('%d%m%y')}-{count + 1:02d}"
        now = datetime.now(timezone.utc)

        invoice_data = {
            'invoice_number': invoice_number,
            'customer_name': data['customer_name'].strip(),
            'contact_name': (data.get('contact_name') or '').strip(),
            'contact_email': (data.get('contact_email') or '').strip(),
            'customer_address': (data.get('customer_address') or '').strip(),
            'attention_to': (data.get('attention_to') or '').strip(),
            'delivery_time': (data.get('delivery_time') or '').strip(),
            'invoice_date': now,
            'due_date': data.get('due_date') or now,
            'items': items,
            'subtotal': round(subtotal, 2),
            'discount_percent': discount_pct,
            'discount_amount': discount_amt,
            'tax_percent': tax_percent,
            'tax_amount': tax_amount,
            'total': total,
            'status': data.get('status', 'draft'),
            'notes': (data.get('notes') or '').strip(),
            'company_id': ObjectId(company_id),
            'created_by': ObjectId(user_id) if isinstance(user_id, str) else user_id,
        }

        invoice_id = InvoiceModel.create(invoice_data)
        logger.info('Invoice created: %s (id=%s, company=%s, total=%.2f, by=%s)', invoice_number, invoice_id, company_id, total, user_id)

        if invoice_data['status'] == 'paid':
            for it in items:
                if not StockService.deduct_stock(it['sku'], it['quantity'], company_id,
                                                  reference=f'Invoice {invoice_number}',
                                                  user_id=user_id):
                    logger.error('Stock deduction failed for SKU=%s on invoice=%s', it['sku'], invoice_number)

        return invoice_id, invoice_number

    @staticmethod
    def update(invoice_id, data, user_id, company_id):
        inv = InvoiceModel.find_by_id(invoice_id)
        if not inv:
            return None
        if str(inv.get('company_id', '')) != company_id:
            return None

        old_status = inv.get('status')
        update_data = {}

        if data.get('status') and data['status'] != old_status:
            update_data['status'] = data['status']
            if data['status'] == 'paid' and old_status != 'paid':
                for it in inv.get('items', []):
                    if not StockService.deduct_stock(it['sku'], it['quantity'], company_id,
                                                      reference=f'Invoice {inv["invoice_number"]} confirmed',
                                                      user_id=user_id):
                        logger.error('Stock deduction failed for SKU=%s on invoice=%s confirm', it['sku'], invoice_id)
        if data.get('notes'):
            update_data['notes'] = data['notes'].strip()
        if data.get('customer_name'):
            update_data['customer_name'] = data['customer_name'].strip()
        if 'contact_name' in data:
            update_data['contact_name'] = data['contact_name'].strip()
        if 'contact_email' in data:
            update_data['contact_email'] = data['contact_email'].strip()
        if 'attention_to' in data:
            update_data['attention_to'] = data['attention_to'].strip()
        if 'delivery_time' in data:
            update_data['delivery_time'] = data['delivery_time'].strip()
        if data.get('invoice_date'):
            update_data['invoice_date'] = datetime.fromisoformat(data['invoice_date'])
        if data.get('due_date'):
            update_data['due_date'] = datetime.fromisoformat(data['due_date'])

        if update_data:
            InvoiceModel.update(invoice_id, update_data)
            logger.info('Invoice updated: %s (id=%s, by=%s)', inv['invoice_number'], invoice_id, user_id)

        return True

    @staticmethod
    def get_by_id(invoice_id):
        inv = InvoiceModel.find_by_id(invoice_id)
        return InvoiceModel.to_dict(inv) if inv else None

    @staticmethod
    def list(page, per_page, filters=None, company_id=None):
        query = filters or {}
        if company_id:
            query['company_id'] = ObjectId(company_id)
        items, total = InvoiceModel.find_all(page, per_page, query)
        return [InvoiceModel.to_dict(item) for item in items], total

    @staticmethod
    def get_recent(limit=5, company_id=None):
        filters = {}
        if company_id:
            filters['company_id'] = ObjectId(company_id)
        items = InvoiceModel.recent(limit, filters)
        return [InvoiceModel.to_dict(item) for item in items]

    @staticmethod
    def get_counts(company_id=None):
        filters = {}
        if company_id:
            filters['company_id'] = ObjectId(company_id)
        total = InvoiceModel.count(filters)
        draft = InvoiceModel.count({**filters, 'status': 'draft'})
        sent = InvoiceModel.count({**filters, 'status': 'sent'})
        paid = InvoiceModel.count({**filters, 'status': 'paid'})
        cancelled = InvoiceModel.count({**filters, 'status': 'cancelled'})
        return {
            'total': total,
            'draft': draft,
            'sent': sent,
            'paid': paid,
            'cancelled': cancelled,
        }

    @staticmethod
    def get_month_sales(company_id=None):
        now = datetime.now(timezone.utc)
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        match = {'status': 'paid', 'created_at': {'$gte': start}}
        if company_id:
            match['company_id'] = ObjectId(company_id)
        result = list(mongo.db[InvoiceModel.collection].aggregate([
            {'$match': match},
            {'$group': {'_id': None, 'total': {'$sum': '$total'}}},
        ]))
        return round(result[0]['total'], 2) if result else 0.0

    @staticmethod
    def get_year_sales(company_id=None):
        now = datetime.now(timezone.utc)
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        match = {'status': 'paid', 'created_at': {'$gte': start}}
        if company_id:
            match['company_id'] = ObjectId(company_id)
        result = list(mongo.db[InvoiceModel.collection].aggregate([
            {'$match': match},
            {'$group': {'_id': None, 'total': {'$sum': '$total'}}},
        ]))
        return round(result[0]['total'], 2) if result else 0.0
