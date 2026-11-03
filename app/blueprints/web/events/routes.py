import logging
from flask import Blueprint, render_template, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.core.models.user_model import UserModel
from app.core.services.event_service import EventService
from app.core.utils.helpers import paginate

logger = logging.getLogger(__name__)
web_events_bp = Blueprint('web_events', __name__, template_folder='../../../templates')


def _get_user():
    """Acting user document, resolved from the database (never claims)."""
    from app.core.utils.context import current_user
    return current_user()


def _company_id():
    """Acting user's company id, resolved from the database (never claims)."""
    from app.core.utils.context import current_company_id
    return current_company_id()


@web_events_bp.route('')
@web_events_bp.route('/')
@jwt_required()
def list_events():
    try:
        page, per_page = paginate(request.args.get('page', 1), request.args.get('per_page', 30))
        filters = {}
        if request.args.get('entity_type'):
            filters['entity_type'] = request.args['entity_type']
        if request.args.get('action'):
            filters['action'] = request.args['action']
        cid = _company_id()
        items, total = EventService.list(page, per_page, filters, cid)
        user = _get_user()
        return render_template('events/list.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               events=items, total=total, page=page, per_page=per_page,
                               pages=(total + per_page - 1) // per_page)
    except Exception:
        logger.exception('Event list error')
        return render_template('events/list.html', mode='web',
                               events=[], total=0, page=1, per_page=30, pages=0)
