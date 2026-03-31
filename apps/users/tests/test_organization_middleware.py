from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from core.middleware import OrganizationMiddleware
from organizations.models import Organization


User = get_user_model()


class OrganizationMiddlewareAuthScopeTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = OrganizationMiddleware(lambda request: HttpResponse("ok"))
        self.org = Organization.objects.create(
            name="Tenant Org",
            code="TEN001",
            schema_name="tenant_org",
        )

    def test_allows_anonymous_access_on_public_site(self):
        request = self.factory.get("/")
        request.user = AnonymousUser()
        request.tenant = None

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)

    def test_requires_login_on_tenant_site(self):
        request = self.factory.get("/")
        request.user = AnonymousUser()
        request.tenant = self.org

        response = self.middleware(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/accounts/login/")

    def test_allows_authenticated_user_on_tenant_site(self):
        user = User.objects.create_user(
            email="tenant-user@example.com",
            username="tenantuser",
            password="password123",
            organization=self.org,
        )
        request = self.factory.get("/")
        request.user = user
        request.tenant = self.org

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)
