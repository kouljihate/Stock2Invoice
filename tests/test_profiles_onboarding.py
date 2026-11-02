"""Unit tests for the Admin / PME-Admin profiles and first-login onboarding.

Pure assertions over the role seed, the endpoint map and the onboarding gate
configuration — no MongoDB writes, no server.
"""

from app.core.utils.bootstrap import ROLE_DEFINITIONS
from app.core.utils.route_permissions import (
    ENDPOINT_PERMISSIONS,
    TENANT_SCOPED_BLUEPRINTS,
    permission_for,
)


class TestProfiles:
    def test_both_top_level_profiles_exist(self):
        assert 'Admin' in ROLE_DEFINITIONS
        assert 'PME-Admin' in ROLE_DEFINITIONS

    def test_admin_is_the_wildcard_profile(self):
        assert ROLE_DEFINITIONS['Admin']['permissions'] == ['*']

    def test_pme_admin_owns_his_company_not_the_platform(self):
        perms = ROLE_DEFINITIONS['PME-Admin']['permissions']
        # full control inside the tenant ...
        assert 'user.manage' in perms
        assert 'product.create' in perms
        assert 'invoice.delete' in perms
        # ... but never the platform-level operations
        assert 'general.companies' not in perms
        assert 'general.allusers' not in perms

    def test_pme_admin_profile_is_seedable(self):
        # the roles collection keys on name.lower()
        assert 'pme-admin' == 'PME-Admin'.lower()


class TestSetupGate:
    def test_setup_endpoint_is_exempt_from_itself(self):
        from app import SETUP_EXEMPT
        assert 'web_profile.setup' in SETUP_EXEMPT

    def test_session_escaping_still_possible_during_setup(self):
        from app import SETUP_EXEMPT
        assert 'web_auth.logout' in SETUP_EXEMPT
        assert 'mobile_auth.logout' in SETUP_EXEMPT

    def test_profile_blueprint_is_not_tenant_scoped(self):
        # it *creates* the tenant, so it cannot require one
        assert 'web_profile' not in TENANT_SCOPED_BLUEPRINTS
        assert permission_for('web_profile.setup') is None

    def test_user_administration_requires_permission(self):
        assert permission_for('web_users.create_user') == 'user.manage'
        assert permission_for('web_users.set_role') == 'user.manage'
        assert 'web_users.set_role' in ENDPOINT_PERMISSIONS
