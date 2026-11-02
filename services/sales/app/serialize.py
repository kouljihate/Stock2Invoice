"""Public document shapes — exact ports of the monolith's model ``to_dict``."""

from si_common.ids import as_str, iso


def customer_out(c):
    if not c:
        return None
    return {
        'id': str(c['_id']),
        'type': c.get('type', 'prive'),
        'name': c.get('name'),
        'contact': c.get('contact', ''),
        'email': c.get('email', ''),
        'phone': c.get('phone', ''),
        'address': c.get('address', ''),
        'city': c.get('city', ''),
        'paiement_terms': c.get('paiement_terms', ''),
        'ICE': c.get('ICE', ''),
        'RC': c.get('RC', ''),
        'company_id': as_str(c.get('company_id')),
        'created_at': iso(c.get('created_at')),
    }


def quote_out(q):
    if not q:
        return None
    return {
        'id': str(q['_id']),
        'quote_number': q.get('quote_number'),
        'customer_name': q.get('customer_name'),
        'contact_name': q.get('contact_name', ''),
        'contact_email': q.get('contact_email', ''),
        'customer_address': q.get('customer_address', ''),
        'customer_city': q.get('customer_city', ''),
        'items': q.get('items', []),
        'subtotal': float(q.get('subtotal', 0)),
        'discount_percent': float(q.get('discount_percent', 0)),
        'discount_amount': float(q.get('discount_amount', 0)),
        'tax_percent': float(q.get('tax_percent', 0)),
        'tax_amount': float(q.get('tax_amount', 0)),
        'total': float(q.get('total', 0)),
        'status': q.get('status', 'draft'),
        'valid_until': iso(q.get('valid_until')),
        'notes': q.get('notes', ''),
        'company_id': as_str(q.get('company_id')),
        'created_by': as_str(q.get('created_by')),
        'created_at': iso(q.get('created_at')),
        'generated_order_id': as_str(q.get('generated_order_id')),
        'generated_order_number': q.get('generated_order_number'),
    }


def order_out(order):
    if not order:
        return None
    return {
        'id': str(order['_id']),
        'order_number': order.get('order_number'),
        'customer_name': order.get('customer_name'),
        'contact_name': order.get('contact_name', ''),
        'contact_email': order.get('contact_email', ''),
        'customer_address': order.get('customer_address', ''),
        'items': order.get('items', []),
        'subtotal': float(order.get('subtotal', 0)),
        'discount_percent': float(order.get('discount_percent', 0)),
        'discount_amount': float(order.get('discount_amount', 0)),
        'tax_percent': float(order.get('tax_percent', 0)),
        'tax_amount': float(order.get('tax_amount', 0)),
        'total': float(order.get('total', 0)),
        'status': order.get('status', 'pending'),
        'notes': order.get('notes', ''),
        'generated_invoice_id': as_str(order.get('generated_invoice_id')),
        'generated_invoice_number': order.get('generated_invoice_number'),
        'company_id': as_str(order.get('company_id')),
        'created_by': as_str(order.get('created_by')),
        'created_at': iso(order.get('created_at')),
    }


def delivery_note_out(dn):
    if not dn:
        return None
    return {
        'id': str(dn['_id']),
        'dn_number': dn.get('dn_number'),
        'order_id': as_str(dn.get('order_id')),
        'order_number': dn.get('order_number', ''),
        'customer_name': dn.get('customer_name', ''),
        'items': dn.get('items', []),
        'notes': dn.get('notes', ''),
        'company_id': as_str(dn.get('company_id')),
        'created_by': as_str(dn.get('created_by')),
        'created_at': iso(dn.get('created_at')),
    }


def invoice_out(inv):
    if not inv:
        return None
    return {
        'id': str(inv['_id']),
        'invoice_number': inv.get('invoice_number'),
        'customer_name': inv.get('customer_name'),
        'contact_name': inv.get('contact_name', ''),
        'contact_email': inv.get('contact_email', ''),
        'customer_address': inv.get('customer_address', ''),
        'customer_city': inv.get('customer_city', ''),
        'customer_country': inv.get('customer_country', ''),
        'attention_to': inv.get('attention_to', ''),
        'delivery_time': inv.get('delivery_time', ''),
        'invoice_date': iso(inv.get('invoice_date')),
        'due_date': iso(inv.get('due_date')),
        'items': inv.get('items', []),
        'subtotal': float(inv.get('subtotal', 0)),
        'discount_percent': float(inv.get('discount_percent', 0)),
        'discount_amount': float(inv.get('discount_amount', 0)),
        'tax_percent': float(inv.get('tax_percent', 0)),
        'tax_amount': float(inv.get('tax_amount', 0)),
        'total': float(inv.get('total', 0)),
        'status': inv.get('status', 'draft'),
        'notes': inv.get('notes', ''),
        'company_id': as_str(inv.get('company_id')),
        'created_by': as_str(inv.get('created_by')),
        'created_at': iso(inv.get('created_at')),
    }
