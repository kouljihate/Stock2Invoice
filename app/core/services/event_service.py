from app.core.models.event_model import EventModel


class EventService:
    @staticmethod
    def record(company_id, entity_type, entity_id, entity_number, action, changes=None, user_id=None, user_name=''):
        from bson.objectid import ObjectId
        data = {
            'company_id': ObjectId(company_id) if company_id else None,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'entity_number': entity_number,
            'action': action,
            'changes': changes or {},
            'user_id': ObjectId(user_id) if user_id else None,
            'user_name': user_name,
        }
        EventModel.create(data)

    @staticmethod
    def list(page, per_page, filters=None, company_id=None):
        query = filters or {}
        if company_id:
            from bson.objectid import ObjectId
            query['company_id'] = ObjectId(company_id)
        items, total = EventModel.find_all(page, per_page, query)
        return [EventModel.to_dict(item) for item in items], total
