import logging

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.core.models.user_model import UserModel
from app.core.models.company_model import CompanyModel
from app.core.services.event_service import EventService
from app.core.utils.uploads import save_logo, UploadError

logger = logging.getLogger(__name__)
web_profile_bp = Blueprint('web_profile', __name__, template_folder='../../../templates')

# Information the PME-Admin must provide on first login: about himself and
# about his company. Legal IDs can be completed later from the company
# settings; the logo is optional here but captured while we have the form.
REQUIRED_PERSONAL = (('name', 'Name'), ('phone', 'Phone'))
REQUIRED_COMPANY = (
    ('company_name', 'Company name'),
    ('address', 'Address'),
    ('city', 'City'),
    ('company_phone', 'Company phone'),
)


def _slugify(name):
    import re
    base = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-') or 'company'
    slug, n = base, 1
    while CompanyModel.find_by_slug(slug):
        n += 1
        slug = f'{base}-{n}'
    return slug


def _render(user_dict, values=None):
    return render_template('profile/setup.html', mode='web', user=user_dict,
                           values=values or {})


@web_profile_bp.route('/setup', methods=['GET', 'POST'])
@jwt_required()
def setup():
    uid = get_jwt_identity()
    user = UserModel.find_by_id(uid)
    if not user:
        flash('Please log in again.', 'danger')
        return redirect(url_for('web_auth.login'))

    if user.get('company_id'):
        # Already completed — never re-run the wizard.
        return redirect(url_for('web_dashboard.index'))

    user_dict = UserModel.to_dict(user)

    if request.method == 'GET':
        return _render(user_dict, {
            'name': user.get('name') or '',
            'phone': user.get('phone') or '',
            'company_email': user.get('email') or '',
        })

    form = request.form
    values = {k: (form.get(k) or '').strip()
              for k in ('name', 'phone', 'company_name', 'address', 'city',
                        'company_phone', 'company_email', 'contact_name',
                        'ice', 'rc', 'if_tax', 'cnss', 'patente', 'website')}

    errors = [f'{label} is required.' for key, label in REQUIRED_PERSONAL + REQUIRED_COMPANY
              if not values[key]]
    if values['website'] and not values['website'].startswith(('http://', 'https://')):
        errors.append('Website must start with http:// or https://')

    # The logo is optional, but a bad file must fail the form rather than be
    # silently dropped.
    logo_filename = None
    try:
        logo_filename = save_logo(request.files.get('logo'))
    except UploadError as exc:
        errors.append(str(exc))

    if errors:
        for e in errors:
            flash(e, 'danger')
        return _render(user_dict, values)

    company_id = CompanyModel.create({
        'name': values['company_name'],
        'slug': _slugify(values['company_name']),
        'logo': logo_filename or '',
        'address': values['address'],
        'city': values['city'],
        'phone': values['company_phone'],
        'email': values['company_email'] or user.get('email') or '',
        'contact_name': values['contact_name'] or values['name'],
        'ice': values['ice'],
        'rc': values['rc'],
        'if_tax': values['if_tax'],
        'cnss': values['cnss'],
        'patente': values['patente'],
        'website': values['website'],
        'invoice_template': {},
        'created_by': uid,
    })

    from bson.objectid import ObjectId
    UserModel.update(uid, {
        'company_id': ObjectId(company_id),
        'name': values['name'],
        'phone': values['phone'],
    })
    # The setup itself is worth recording: it is the moment the tenant comes
    # into existence.
    EventService.record(
        company_id, 'company', company_id, values['company_name'], 'setup',
        user_id=uid, user_name=values['name'],
    )
    logger.info('PME-Admin %s completed company setup: %s',
                user.get('email'), values['company_name'])
    flash(f'Welcome, {values["name"]}! Your company "{values["company_name"]}" is ready.', 'success')
    return redirect(url_for('web_dashboard.index'))


@web_profile_bp.route('/edit', methods=['GET', 'POST'])
@jwt_required()
def edit():
    """Let the signed-in user maintain his own profile."""
    uid = get_jwt_identity()
    user = UserModel.find_by_id(uid)
    if not user:
        flash('Please log in again.', 'danger')
        return redirect(url_for('web_auth.login'))

    user_dict = UserModel.to_dict(user)
    values = {'name': user.get('name') or '', 'phone': user.get('phone') or ''}

    if request.method == 'GET':
        return render_template('profile/edit.html', mode='web', user=user_dict,
                               values=values)

    values['name'] = (request.form.get('name') or '').strip()
    values['phone'] = (request.form.get('phone') or '').strip()

    if not values['name']:
        flash('Name is required.', 'danger')
        return render_template('profile/edit.html', mode='web', user=user_dict,
                               values=values)

    UserModel.update(uid, {'name': values['name'], 'phone': values['phone']})
    logger.info('Profile updated for %s', user.get('email'))
    flash('Your profile has been updated.', 'success')
    return redirect(url_for('web_profile.edit'))
