"""Public document shapes — exact ports of the monolith's model ``to_dict``."""

from si_common.ids import iso, as_str


def product_out(item):
    if not item:
        return None
    return {
        'id': str(item['_id']),
        'name': item.get('name'),
        'sku': item.get('sku'),
        'description': item.get('description', ''),
        'quantity': item.get('quantity', 0),
        'price': float(item.get('price', 0)),
        'purchase_price': float(item.get('purchase_price', 0)),
        'category': item.get('category', ''),
        'subcategory': item.get('subcategory', ''),
        'package_type': item.get('package_type', ''),
        'brand': item.get('brand', ''),
        'supplier_id': str(item.get('supplier_id')) if item.get('supplier_id') else '',
        'supplier_name': item.get('supplier_name', ''),
        'pack_size': float(item.get('pack_size', 0)),
        'pack_size_unit': item.get('pack_size_unit', ''),
        'number_of_pack': int(item.get('number_of_pack', 0)),
        'quantity_min': int(item.get('quantity_min', 5)),
        'status': item.get('status', 'active'),
        'photos': item.get('photos', []),
        'company_id': as_str(item.get('company_id')),
        'created_at': iso(item.get('created_at')),
        'updated_at': iso(item.get('updated_at')),
    }


def movement_out(mv):
    if not mv:
        return None
    return {
        'id': str(mv['_id']),
        'product_id': str(mv.get('product_id')),
        'product_name': mv.get('product_name', ''),
        'sku': mv.get('sku', ''),
        'type': mv.get('type'),
        'quantity': mv.get('quantity', 0),
        'quantity_before': mv.get('quantity_before', 0),
        'quantity_after': mv.get('quantity_after', 0),
        'reason': mv.get('reason', ''),
        'reference': mv.get('reference', ''),
        'company_id': as_str(mv.get('company_id')),
        'created_by': as_str(mv.get('created_by')),
        'created_at': iso(mv.get('created_at')),
    }
