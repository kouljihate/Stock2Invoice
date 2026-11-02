"""Unit tests for the authorization and multi-tenancy primitives.

These are pure-function tests: no server, no MongoDB writes.
"""

from datetime import datetime, timedelta, timezone

from app.config import Config
from app.core.utils.helpers import tenant_filter
from app.core.utils.permissions import (
    ALL_PERMISSIONS,
    expand_permission,
    get_effective_permissions,
    has_permission,
)
from app.core.utils.rate_limit import check_rate_limit, reset_limits
from app.core.utils.route_permissions import (
    ENDPOINT_PERMISSIONS,
    TENANT_SCOPED_BLUEPRINTS,
    permission_for,
)


class TestPermissionExpansion:
    def test_star_expands_to_every_permission(self):
        assert expand_permission('*') == ALL_PERMISSIONS

    def test_module_wildcard_only_covers_that_module(self):
        expanded = expand_permission('product.*')
        assert expanded
        assert all(p.startswith('product.') for p in expanded)
        assert 'invoice.view' not in expanded

    def test_exact_permission_passes_through(self):
        assert expand_permission('invoice.refund') == ['invoice.refund']

    def test_unknown_wildcard_yields_nothing(self):
        assert expand_permission('nosuchmodule.*') == []

    def test_effective_permissions_unions_multiple_roles(self):
        effective = get_effective_permissions(['product.view', 'invoice.*'])
        assert 'product.view' in effective
        assert 'invoice.create' in effective
        assert len(effective) == 1 + len(expand_permission('invoice.*'))


class TestHasPermission:
    def test_exact_match(self):
        assert has_permission(['invoice.view'], 'invoice.view')
        assert not has_permission(['invoice.view'], 'invoice.create')

    def test_module_wildcard(self):
        assert has_permission(['invoice.*'], 'invoice.create')
        assert not has_permission(['invoice.*'], 'order.create')

    def test_global_wildcard(self):
        assert has_permission(['*'], 'general.companies')

    def test_malformed_permission_is_not_granted(self):
        assert not has_permission(['invoice.*'], 'invoice')
        assert not has_permission(['*'], 'invoice')  # not module.op form


class TestRoutePermissionMap:
    def test_unrestricted_endpoints_stay_unrestricted(self):
        for endpoint in ('web_auth.login', 'web_auth.register', 'web_auth.logout',
                         'web_dashboard.index', 'mobile_dashboard.index',
                         'admin.index', 'eshop.index', 'static', 'health'):
            assert permission_for(endpoint) is None, endpoint

    def test_reads_resolve_to_view(self):
        assert permission_for('web_invoices.list_invoices') == 'invoice.view'
        assert permission_for('web_stock.view_product') == 'product.view'
        assert permission_for('mobile_orders.download_pdf') == 'order.view'

    def test_writes_resolve_to_their_operation(self):
        assert permission_for('web_invoices.create_invoice') == 'invoice.create'
        assert permission_for('web_stock.edit_product') == 'product.edit'
        assert permission_for('web_suppliers.delete_supplier') == 'supplier.delete'
        assert permission_for('web_purchase_orders.send_order') == 'purchase_order.send'
        assert permission_for('web_supplier_invoices.invalidate_invoice') == 'supplier_invoice.validate'

    def test_overrides_win_over_the_derived_value(self):
        assert permission_for('web_users.create_user') == 'user.manage'
        assert permission_for('web_users.set_role') == 'user.manage'
        assert permission_for('web_events.list_events') == 'general.activities'

    def test_every_mapped_permission_exists_in_the_catalog(self):
        for endpoint in ENDPOINT_PERMISSIONS:
            assert permission_for(endpoint) in ALL_PERMISSIONS, endpoint

    def test_derived_permissions_exist_in_the_catalog(self):
        from app import app
        for rule in app.url_map.iter_rules():
            permission = permission_for(rule.endpoint)
            if permission:
                assert permission in ALL_PERMISSIONS, (rule.endpoint, permission)

    def test_tenant_scoped_set_only_covers_business_blueprints(self):
        # Dashboards, auth, admin and eShop must never require a company.
        assert 'web_dashboard' not in TENANT_SCOPED_BLUEPRINTS
        assert 'web_users' not in TENANT_SCOPED_BLUEPRINTS
        assert 'admin' not in TENANT_SCOPED_BLUEPRINTS
        assert 'eshop' not in TENANT_SCOPED_BLUEPRINTS
        assert 'web_invoices' in TENANT_SCOPED_BLUEPRINTS
        assert 'mobile_stock' in TENANT_SCOPED_BLUEPRINTS


class TestTenantFilter:
    def test_matches_nothing_without_a_company(self):
        assert tenant_filter(None) == {'company_id': {'$in': []}}
        assert tenant_filter('') == {'company_id': {'$in': []}}

    def test_rejects_a_malformed_id_instead_of_widening(self):
        # A bad id must never degrade into an unscoped query.
        assert tenant_filter('not-an-objectid') == {'company_id': {'$in': []}}

    def test_scopes_to_the_company(self):
        from bson.objectid import ObjectId
        cid = '507f1f77bcf86cd799439011'
        result = tenant_filter(cid)
        assert result == {'company_id': ObjectId(cid)}

    def test_custom_field(self):
        assert tenant_filter(None, 'owner_id') == {'owner_id': {'$in': []}}


class TestRateLimit:
    def test_allows_up_to_the_limit_then_blocks(self):
        reset_limits()
        limit, window = 3, 60
        key = 'unit-test-limit'
        assert [check_rate_limit(key, limit, window) for _ in range(limit)] == [False] * limit
        assert check_rate_limit(key, limit, window) is True

    def test_keys_are_independent(self):
        reset_limits()
        assert check_rate_limit('a', 1, 60) is False
        assert check_rate_limit('b', 1, 60) is False
        assert check_rate_limit('a', 1, 60) is True

    def test_window_expiry_frees_the_bucket(self, monkeypatch):
        reset_limits()
        key = 'unit-test-window'
        assert check_rate_limit(key, 1, 60) is False
        assert check_rate_limit(key, 1, 60) is True

        import app.core.utils.rate_limit as rl
        now = datetime.now(timezone.utc)
        real_time = rl.time.monotonic
        monkeypatch.setattr(rl.time, 'monotonic', lambda: real_time() + 61)
        assert check_rate_limit(key, 1, 60) is False


class TestSecretValidation:
    def test_placeholders_are_flagged(self):
        class Placeholder(Config):
            SECRET_KEY = 'change-this-to-a-random-secret-key'
            JWT_SECRET_KEY = 'jwt-dev-secret'

        problems = Placeholder.insecure_secrets()
        assert len(problems) == 2
        assert any('placeholder' in p for p in problems)

    def test_short_hs256_key_is_flagged(self):
        class Short(Config):
            SECRET_KEY = 'x' * 31
            JWT_SECRET_KEY = 'y' * 31

        problems = Short.insecure_secrets()
        assert len(problems) == 2
        assert any('31 bytes' in p for p in problems)

    def test_strong_secrets_pass(self):
        class Strong(Config):
            SECRET_KEY = 'a' * 64
            JWT_SECRET_KEY = 'b' * 64

        assert Strong.insecure_secrets() == []
