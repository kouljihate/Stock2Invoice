from app.models.stock import StockModel


class StockService:

    @staticmethod
    def validate(data):
        errors = []
        name = (data.get('name') or '').strip()
        if not name:
            errors.append('Product name is required.')

        sku = (data.get('sku') or '').strip()
        if not sku:
            errors.append('SKU is required.')

        qty = data.get('quantity', 0)
        try:
            qty = int(qty)
            if qty < 0:
                errors.append('Quantity cannot be negative.')
        except (ValueError, TypeError):
            errors.append('Quantity must be an integer.')

        price = data.get('price', 0)
        try:
            price = float(price)
            if price < 0:
                errors.append('Unit price cannot be negative.')
        except (ValueError, TypeError):
            errors.append('Unit price must be a number.')

        return errors, {
            'name': name,
            'sku': sku,
            'description': (data.get('description') or '').strip(),
            'quantity': qty,
            'price': price,
            'category': (data.get('category') or '').strip(),
        }

    @staticmethod
    def create(data):
        return StockModel.create(data)

    @staticmethod
    def get_by_id(stock_id):
        return StockModel.find_by_id(stock_id)

    @staticmethod
    def list(page, per_page, filters=None):
        items, total = StockModel.find_all(page, per_page, filters)
        return [StockModel.to_dict(item) for item in items], total

    @staticmethod
    def update(stock_id, data):
        StockModel.update(stock_id, data)

    @staticmethod
    def delete(stock_id):
        StockModel.delete(stock_id)

    @staticmethod
    def deduct_stock(sku, quantity):
        from app.extensions import mongo
        result = mongo.db[StockModel.collection].update_one(
            {'sku': sku, 'quantity': {'$gte': quantity}},
            {'$inc': {'quantity': -quantity}}
        )
        return result.modified_count == 1
